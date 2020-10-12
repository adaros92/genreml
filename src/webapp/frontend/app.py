import aiohttp
import asyncio
import hashlib
import json
import os
import uuid
from quart import Quart, request, jsonify, abort, redirect, url_for, url_for, render_template


app = Quart(__name__, static_folder='./static', static_url_path='/static')
event_loop = asyncio.get_event_loop()
filestore_directory = "/filestore"


@app.route('/uploadmultiple', methods=['POST'])
async def file_upload_handler():
    global filestore_directory
    files = (await request.files).getlist("multiFileUploadForm")
    for f in files:
        data = f.read()
        if type(data) == bytes:
            file_hash = hashlib.sha256(data).hexdigest()
            # currently the files are simply written to disk.
            # log term data hash + prediction stored in a database
            # or temporary in memory object store may be a good idea
            # so model is only run on new unknown data.
            # if performance can be guaranteed to be good enough
            # this will be replaced with API call to prediction
            # engine. Otherwise, a token will have to be returned
            # for polling until confirmation that audio processing
            # and prediction work is complete.
            write_path = "/".join([filestore_directory, file_hash])
            if not os.path.isfile(write_path):
                with open(write_path, "wb") as fh:
                    fh.write(data)
    return redirect(url_for('index'))


@app.route('/')
async def index():
    """ Server route for the app's landing page """
    return await render_template('index.html')