FROM 010850123561.dkr.ecr.us-west-2.amazonaws.com/citrine-executor-python

# Add commands here if you want
# Note that these have already been run via onbuild:
# ADD . /usr/local/ingest/compute
# RUN pip install -r requirements.txt
# RUN python ./setup.py install

# This is the standard entrypoint
# Don't change unless you know what you are doing
ENTRYPOINT ["ruby", "../wrap.rb"]
CMD ["--manifest_url=manifest.json"]
