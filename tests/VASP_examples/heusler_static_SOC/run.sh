#!/bin/sh
#PBS -l nodes=1:ppn=16,walltime=500:00:00
#PBS -j oe
#PBS -N LBMO
#PBS -V
#PBS -W stageout=/$TMPDIR/@tardis.cac.cornell.edu:$PBS_O_WORKDIR/
#PBS -m abe -M jobcornell@gmail.com

#####################################################################
#Begin Setup stuff, don't touch
#Check to see if tmpdir is set, if not complain and provide it as /tmp
if [ -z "$TMPDIR" ]; then
        echo "Torque did not set TMPDIR!  Check with your admin, god knows what else is broken"
	TMPDIR=/tmp
	echo "TMPDIR has no been set manually, value: $TMPDIR"
else echo "TMPDIR has been provided by Torque: $TMPDIR"
fi

#Count the number of processeors requested
np=$(wc -l < $PBS_NODEFILE)
#Count the number of nodes requested
nodes=$(uniq $PBS_NODEFILE | wc -l)
#Create a uniqued up nodefile
uniqNodeFile=$TMPDIR/uniqmachinefile
uniq $PBS_NODEFILE > $uniqNodeFile
#Create once per node and once per process alias
alias perHostMpiExec='mpiexec -machinefile $uniqNodeFile -np $nodes'
alias perProcMpiExec='mpiexec -machinefile $PBS_NODEFILE -np $np'

#Start up mpd's one/node
mpdboot -f $uniqNodeFile -r ssh -n $nodes
mpdtrace -l -v
#End Setup Stuff
######################################################################

######################################################################
#Moving data from $HOME to local temporary disk.  This assumes that 
#you typed qsub from the directory where you're input data is.  If you
#have data stored elsewhere, you'll want to edit the DATASOURCE variable
DATASOURCE=$PBS_O_WORKDIR
#First create the temporary directory, explicitely force once per node
#Tmpdir already created by Torque
#perHostMpiExec mkdir $TMPDIR
#if your input data is somewhere other than where you typed qsub, you should
#edit this line to reflect where that input data is located
perHostMpiExec cp $DATASOURCE/* $TMPDIR
######################################################################

######################################################################
#Configuration of process pinning.
#Generally speaking, pinning processes is a good thing, however, if running
#multiple jobs on the same node, you can run into problems as Intel MPI
#assumes that it can start at cpu 0 and walk, which isn't neccesarily true.
#The PIN_CONTROL variables may be set to [PIN | NOPIN | SMARTPIN]
#
#       PIN - allow intel MPI to PIN the processes, useful if ppn = 8 or
#               if the nodes are restricted to one job per node
#       NOPIN - disable intel MPI pinning and put scheduler into "BATCH" mode
#               which should help reduce swapping.  SAFE MODE!
#       SMARTPIN - check to see if there are vasp processes running and if so
#               pin the processes onto cpus offset by the number of running
#               vasp processes.  A bit dangerous and ONLY detects vasp processes.
PIN_CONTROL="NOPIN"

#Control code for pin mode
if [ "$PIN_CONTROL" = "PIN" ];
then
        echo "Enabling Intel MPI fixed pinning"
        export I_MPI_PIN=enable
fi
if [ "$PIN_CONTROL" = "NOPIN" ];
then
        echo "Disabling processor pinning"
        export I_MPI_PIN=disable
        schedtool -3 $$
fi
if [ "$PIN_CONTROL" = "SMARTPIN" ];
then
        echo "Attempting to pin processes on free cpus"
        vasps=$(/sbin/pidof vasp | wc -w)
        export I_MPI_PIN=enable
        export I_MPI_PIN_PROCS=$vasps-7
fi
####################################################################



DATE=`date`
echo ""
echo "Time at the start of the job is: $DATE"
echo ""

######################################################################
#Execute vasp on ALL available processors (ndoes*ppn) from the directory
#where the input data was moved to.  In the UNLIKELY case that you want
#VASP to start from a different location, alter the -wdir value.  This
#is HIGHLY UNLIKELY. 
#Now we execute VASP on every available processoer
echo "Starting up VASP..."

# cd $TMPDIR

for i in  self band

do 
cp $TMPDIR/INCAR-$i $TMPDIR/INCAR
cp $TMPDIR/KPOINTS-$i $TMPDIR/KPOINTS
# perProcMpiExec -wdir $TMPDIR /home/fs03/jh2336/vasp/vasp.5.3.3_ncl/vasp>&$TMPDIR/log
perProcMpiExec -wdir $TMPDIR /home/fs03/jh2336/vasp/vasp.5.2.11_mpi_ncl_forC4/vasp>&$TMPDIR/log
mv $TMPDIR/OUTCAR $TMPDIR/OUTCAR-$i
mv $TMPDIR/OSZICAR $TMPDIR/OSZICAR-$i
cp $TMPDIR/DOSCAR $TMPDIR/DOSCAR-$i
mv $TMPDIR/EIGENVAL $TMPDIR/EIGENVAL-$i
mv $TMPDIR/PROCAR  $TMPDIR/PROCAR-$i


done
rm $TMPDIR/CH*
rm $TMPDIR/WAVE*

#####################################################################
DATE=`date`
echo ""
echo "Time at the end of the job is: $DATE"
echo ""

#####################################################################
#Move results back
#The entire contents of the VASP directory will be copied back to 
#a uniquely named subdirectory of DATASOURCE, which is created here.
#This assumes that all output is collected on the master node, as this
#is only executed therie.
mv -f $TMPDIR/*  $DATASOURCE
rm -fr $TMPDIR
#####################################################################

####################################################################
#START CLEANUP, don't touch
mpdallexit
#clean up the temporary directory
#No need to clean up the tmpdir, Torque cleans it up on it's own
#rm -rf /tmp/$PBS_JOBID
rm -f $uniqNodeFile
####################################################################


