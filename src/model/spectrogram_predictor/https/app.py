from quart import Quart, request, jsonify, abort, redirect, url_for
from collections import Counter
from functools import reduce
from keras import models
from sklearn.preprocessing import LabelEncoder
import asyncio
import autokeras
import base64
import gc
import hashlib
import io
import itsdangerous
import json
import numpy as np
import os
import pandas as pd
import pprint
import re
import shutil
import uuid
import zlib
from model.processing.audio import AudioFile
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import tensorflow as tf
import librosa


app = Quart(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024


class app_state:
    def __init__(self, loop):
        self.loop = loop
        self.model_hash_registry = dict()
        self.model_dir = '/opt/model_store'
        self.temp_file_lock = asyncio.Lock()
        self.signer = itsdangerous.Signer(os.environ['SIGNING_TOKEN'])
        self.serializer = itsdangerous.Serializer(os.environ['SIGNING_TOKEN'])
    # does not need to be async now
    # but tokens could come from API
    # in future
    async def store_model_hash(self, model_hash, load=False):
        if model_hash not in self.model_hash_registry:
            self.model_hash_registry[model_hash] = {
                'hash': model_hash,
                'loaded': False,
                'model': None,
                'lock': asyncio.Lock()
            }

    async def check_model_hash(self, model_hash):
        global APP_STATE
        model_name = "/".join([APP_STATE.model_dir, model_hash])+".h5"
        if model_hash not in self.model_hash_registry:
            if not os.path.isfile(model_name):
                for file in os.listdir('/opt/temp_model_uploads'):
                    if file.endswith('.dat'):
                        with open('/opt/temp_model_uploads/'+file,'rb') as temp:
                            model_hash = hashlib.sha256(temp.read()).hexdigest()
                        shutil.move('/opt/temp_model_uploads/'+file, model_name)
                        await APP_STATE.store_model_hash(model_hash, False)
            else:
                self.store_model_hash(model_hash)
        return model_hash in self.model_hash_registry


async def run_model(model_hash, prediction_data):
    global APP_STATE
    prediction = None
    if model_hash not in APP_STATE.model_hash_registry:
        return None
    # this is slower, but testing to see if resolves potential
    # memory leaks
    model_path = "/".join([APP_STATE.model_dir, model_hash])+".h5"
    if not os.path.isfile(model_path):
        return None
    loaded_model = models.load_model(model_path)
    prediction = loaded_model.predict(prediction_data)
    del(loaded_model)
    gc.collect()
    loaded_model = None
    return prediction


@app.route('/test',methods=['GET'])
async def test_server():
    return jsonify({'msg': 'hey there!'})


async def hash_node_uploads():
    global APP_STATE
    async with APP_STATE.temp_file_lock:
        hashes = []
        for file in os.listdir('/opt/temp_model_uploads'):
            if file.endswith('.dat'):
                with open('/opt/temp_model_uploads/'+file,'rb') as temp:
                    model_hash = hashlib.sha256(temp.read()).hexdigest()
                    if model_hash not in APP_STATE.model_hash_registry:
                        os.remove('/opt/temp_model_uploads/'+file)
                        continue
                    hashes.append(model_hash)
                model_name = "/".join([APP_STATE.model_dir, model_hash])+".h5"
                shutil.move('/opt/temp_model_uploads/'+file, model_name)
                await APP_STATE.store_model_hash(model_hash, False)
        return hashes


@app.route('/hashmodels',methods=['GET'])
async def hash_models():
    hashes = []
    hashes = await hash_node_uploads()
    return jsonify({
        'hashes': hashes
    })


@app.route('/uploadmodel',methods=['POST'])
async def upload_model():
    global APP_STATE
    request_files = await request.files
    if 'model' in request_files:
        model_file = request_files['model']
    else:
        return jsonify({'msg':'incorrectly formatted form'})
    model_bin = None
    model_hash = None
    model_name = None
    try:
        model_bin = model_file.read()
        if APP_STATE.signer.validate(model_bin):
            model_bin = APP_STATE.signer.unsign(model_bin)
        else:
            return jsonify({'msg': 'no valid signature on data'})
        model_hash = hashlib.sha256(model_bin).hexdigest()
        model_name = "/".join([APP_STATE.model_dir, model_hash])+".h5"
        with open(model_name, "wb") as mod:
            mod.write(model_bin)
        await APP_STATE.store_model_hash(model_hash, False)
    except Exception as ex:
        return jsonify({
            'msg': 'saving model failed',
            'ex': str(ex)
        })
        pass
    if model_hash is not None:
        return jsonify({
            'msg': 'model saved',
            'hash': model_hash
        })
    return jsonify({'msg':'something went wrong'})


@app.route('/registermodelhash', methods=['POST'])
async def register_model_hash():
    global APP_STATE
    model_hash = None
    prediction_data = None
    req_data = await request.get_data()
    try:
        req_json = APP_STATE.serializer.loads(req_data)
        if 'hash' in req_json:
            model_hash = req_json['hash']
            await APP_STATE.store_model_hash(model_hash, False)
            return jsonify({'msg': 'model hash stored'})
    except Exception as ex:
        return jsonify({
            'msg': 'payload did not have valid signature',
            'ex': str(ex)
        })
    return jsonify({'msg': 'something went wrong'})


@app.route('/prediction', methods=['POST'])
async def get_prediction():
    global APP_STATE
    model_hash = None
    prediction_data = None
    req_data = await request.get_data()
    try:
        req_json = APP_STATE.serializer.loads(req_data)
    except Exception as ex:
        return jsonify({
            'msg': 'payload did not have valid signature',
            'ex': str(ex)
            })
    if 'model_hash' in req_json and 'data' in req_json and 'ext' in req_json:
        data = req_json['data']
        # get csv row
        csv_b_buf = io.BytesIO(base64.b64decode(req_json['csv']))
        # construct data from csv because order of data
        # most match from model training to prediction
        df_row = pd.read_csv(csv_b_buf, index_col=0)
        # create np array for prediction call
        np_row = df_row.to_numpy(dtype=np.float32)
        # this will be audio
        raw_data = base64.b64decode(data)
        data_hash = hashlib.sha256(raw_data).hexdigest()
        with open(data_hash+'.'+req_json['ext'], 'wb') as f:
            f.write(raw_data)
        file_location = data_hash+'.'+req_json['ext']
        audio_signal, sample_rate = librosa.load(file_location)
        # use convenience library
        af = AudioFile(file_location, audio_signal, sample_rate)
        dest = af.to_spectrogram(file_location)
        with open(dest, 'rb') as ifile:
            raw_image = ifile.read()
        img_width = 335
        img_height = 200
        img = Image.open(dest).convert('L')
        img = img.crop((55, 50, 390, 250))
        img = img.resize((img_width, img_height))
        # turn image data into np array
        img_array = np.array(img)
        model_hash = req_json['model_hash']
    if await APP_STATE.check_model_hash(model_hash):
        try:
            prediction = await run_model(model_hash,[np_row, np.array([img_array])])
        except Exception as ex:
            return jsonify({
                'msg': 'model prediction caused an exception',
                'ex': str(ex)
            })
        if prediction is None:
            return jsonify({
                'msg': 'attempt to load and run model failed'
            })
        return_object = {
            'array': prediction.tolist()
        }
        return jsonify(return_object)
    else:
        return jsonify({
            'msg':'model not found'
        })
    return jsonify({'msg':'something went wrong'})


# this deals with problem that sometimes
# async scheduler may not be "awake" and
# may not schedule some pending tasks.
# also we can put different state checks
# here and take action if state is bad
# or some type of internal state update
# must be performed
async def watcher():
    try:
        await hash_node_uploads()
    except Exception as ex:
        pass
    await asyncio.sleep(10)


event_loop = None
APP_STATE = None
@app.before_serving
async def start():
    global event_loop
    global APP_STATE
    event_loop = asyncio.get_event_loop()
    APP_STATE = app_state(event_loop)
    event_loop.create_task(watcher())
