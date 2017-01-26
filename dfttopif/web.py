import sys
import json
import logging
import requests
from pypif import pif
from flask import Flask, request
from flask_cors import CORS
from dfttopif import *


# Configure flask
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


@app.route('/convert/from/tarfile', methods=['POST'])
def convert_from_tarfile():
    # Create a temporary directory to save the files and cleanup when
    # finished with it
    temp_dir_name = '/tmp/' + str(uuid.uuid4())
    os.makedirs(temp_dir_name)
    try:
        data = json.loads(request.get_data(as_text=True))
        response = requests.get(data['url'], stream=True)
        filename = temp_dir_name + '/file_to_process'
        with open(filename, 'wb') as output:
            shutil.copyfileobj(response.raw, output)
        return pif.dumps({'system': tarfile_to_pif(filename, '/tmp/')})
    finally:
        shutil.rmtree(temp_dir_name)
