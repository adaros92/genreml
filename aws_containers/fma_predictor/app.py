from quart import Quart, request, jsonify, abort, redirect, url_for
from collections import Counter
from functools import reduce
from keras import models
from sklearn.preprocessing import LabelEncoder
import asyncio
import base64
import gc
import hashlib
import httpx
import io
import itsdangerous
import json
import numpy as np
import os
import pandas as pd
import pickle
import pprint
import re
import requests
import shutil
import sys
import uuid
import zlib
import dns.resolver as resolver
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import tensorflow as tf
from PIL import Image
import audio_classifier as classy


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
        if not os.path.isfile(model_name):
            if model_hash in self.model_hash_registry:
                for file in os.listdir('/opt/temp_model_uploads'):
                    if file.endswith('.dat'):
                        with open('/opt/temp_model_uploads/'+file,'rb') as temp:
                            file_hash = hashlib.sha256(temp.read()).hexdigest()
                            if file_hash == model_hash:
                                shutil.move('/opt/temp_model_uploads/'+file, model_name)
                                await APP_STATE.store_model_hash(model_hash, False)
                                return True
                            else:
                                os.remove('/opt/temp_model_uploads/'+file)
        return os.path.isfile(model_name)

    def get_srv_record_url(self, port_key, address_key, schema_key, test_endpoint=True):
        srv_schema = os.environ[schema_key]
        srv_address = os.environ[address_key]
        srv_url = srv_schema+"://"+os.environ[address_key]
        if port_key in os.environ:
            srv_url += ":"+os.environ[port_key]
        try:
            resolve_service_url = resolver.query(srv_address, 'SRV')
            srv_address = re.split('\s+', resolve_service_url.rrset.to_text())[-1].strip('.')
            srv_url = srv_schema+"://"+re.split('\s+', resolve_service_url.rrset.to_text())[-1].strip('.')
            if port_key in os.environ:
                srv_url += ":"+os.environ[port_key]
            if test_endpoint:
                req_test = requests.get(srv_url+"/test")
                req_test.raise_for_status()
        except Exception as ex:
            eprint(str(ex))
            # in most cases this is likely to be the wrong url
            srv_url = srv_schema+"://"+os.environ[address_key]
            if port_key in os.environ:
                srv_url += ":"+os.environ[port_key]
            pass
        return srv_url


# simple logging snippet from https://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, flush=True, **kwargs)


async def run_model(model_hash, prediction_data):
    global APP_STATE
    prediction = None
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
        eprint(str(ex))
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
        eprint(str(ex))
        return jsonify({
            'msg': 'payload did not have valid signature',
            'ex': str(ex)
        })
    return jsonify({'msg': 'something went wrong'})


async def feature_spectrogram_uploads(raw_data, ext):
    global APP_STATE
    song_upload = {
        'ext': ext,
        'data': base64.b64encode(raw_data).decode('utf-8'),
    }
    async with httpx.AsyncClient() as client:
        try:
            features = await client.post(APP_STATE.get_srv_record_url('GENREML_FEATURES_PORT', 'GENREML_FEATURES_ADDRESS', 'GENREML_FEATURES_SCHEMA', False)+'/requestfeatures', data=APP_STATE.serializer.dumps(song_upload), timeout=600.0)
            features.raise_for_status()
        except Exception as ex:
            eprint("failure in features api call")
            eprint(str(ex))
            return (False, dict(),dict())
        try:
            spectrograms = await client.post(APP_STATE.get_srv_record_url('GENREML_SPECTRO_PORT', 'GENREML_SPECTRO_ADDRESS', 'GENREML_SPECTRO_SCHEMA', False)+'/melspectrogram', data=APP_STATE.serializer.dumps(song_upload), timeout=600.0)
            spectrograms.raise_for_status()
        except Exception as ex:
            eprint("failure in spectrograms api call")
            eprint(str(ex))
            return (False, dict(),dict())
        try:
            features = features.json()
            if 'ex' in features:
                eprint('problem with clip features request')
                eprint(features['ex'])
            if 'msg' in features:
                eprint(features['msg'])
            spectrograms = spectrograms.json()
            if 'ex' in spectrograms:
                eprint('problem with clip spectrograms request')
                eprint(spectrograms['ex'])
            if 'msg' in spectrograms:
                eprint(spectrograms['ex'])
            spectrogram = {'data':base64.b64decode(spectrograms['image'])}
            return (True, features, spectrogram)
        except Exception as ex:
            eprint("failure in spectrogram and feature parsing after return from api calls")
            eprint(str(ex))
            return (False, dict(),dict())
    return (False, dict(),dict())


def get_uid():
    return str(uuid.uuid4()).replace('-', '')


@app.route('/prediction', methods=['POST'])
async def get_prediction():
    global APP_STATE
    cleanup_paths = []
    def cleanup_files():
        for path in cleanup_paths:
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except Exception as ex:
                eprint(str(ex))
                pass
    eprint("prediction request received")
    model_hash = None
    prediction_data = None
    req_data = await request.get_data()
    try:
        eprint("deserializing")
        req_json = APP_STATE.serializer.loads(req_data)
    except Exception as ex:
        eprint(str(ex))
        cleanup_files()
        return jsonify({
            'msg': 'payload did not have valid signature',
            'ex': str(ex)
            })
    if 'model_hash' not in req_json or 'data' not in req_json or 'ext' not in req_json:
        eprint("model_hash, data, or ext not found in requset")
        return jsonify({
            'ex':'model_hash, data, or ext not found in requset',
            'msg':'request missing necessary fields'
        })
    try:
        eprint('request handling starting')
        data = req_json['data']
        # this will be audio
        raw_data = base64.b64decode(data)
        data_uid = get_uid()
        upload_path = data_uid+'.'+req_json['ext']
        with open(upload_path, 'wb') as f:
            f.write(raw_data)
        cleanup_paths.append(upload_path)
        eprint("defining class")
        song_class = classy.Song()
        song_class.path = upload_path
        eprint("extracting song data")
        song_class.extract_song_data()
        clip_uids = list()
        eprint("starting clips")
        for clip in song_class.clips:
            try:
                eprint("writing clip")
                uid = get_uid()
                # export wav file
                scaled = np.int16(clip / np.max(np.abs(clip)) * 32767)
                classy.write(uid+"."+req_json['ext'], song_class.sr, scaled)
                clip_uids.append(uid+"."+req_json['ext'])
                cleanup_paths.append(uid+"."+req_json['ext'])
            except Exception as ex:
                eprint('clip save failed')
                eprint(ex)
                pass
        clip_data = list()
        eprint("getting features and spectrograms")
        for path in clip_uids:
            clip_data.append(await feature_spectrogram_uploads(raw_data, req_json['ext']))
        clip_exception_store = []
        eprint("processing features and spectrograms")
        for processed in clip_data:
            try:
                features = processed[1]
                spectrogram = processed[2]
                if processed[0] is False:
                    if 'ex' in features:
                        eprint(features['ex'])
                        clip_exception_store.append(features['ex'])
                        continue
                    if 'ex' in spectrogram:
                        eprint(spectrogram['ex'])
                        clip_exception_store.append(spectrogram['ex'])
                        continue
                    eprint('failed to process a clip')
                    continue
                eprint("writing gray scale image")
                spectrogram = spectrogram['data']
                gray_path = get_uid()+'.gray.png'
                with open(gray_path,'wb') as f:
                    f.write(spectrogram)
                cleanup_paths.append(gray_path)
                img_width = 335
                img_height = 200
                img = Image.open(gray_path).convert('L')
                img = img.crop((55, 50, 390, 250))
                img = img.resize((img_width, img_height))
                img_data = list(img.getdata())
                song_class.spectrograms.append(img_data)
                if not isinstance(features, dict):
                    features = json.loads(features)
                eprint("creating series")
                series = pd.Series(features)
                # code from audio-classifier
                features_sorted = []
                for col in classy.FEATURE_COLS:
                    features_sorted.append(features[col])
                features_sorted = np.array(features_sorted)
                features_sorted = features_sorted[np.newaxis, :]
                # load scaler object from binary exported from trained data
                sc = pickle.load(open('./std_scaler_B.pkl', 'rb'))
                features = sc.transform(features_sorted)[0]
                song_class.features.append(features)
                continue
            except Exception as ex:
                eprint('error in clip processing')
                clip_exception_store.append(ex)
                pass
        for x in clip_exception_store:
            eprint(str(x))
        if len(clip_exception_store) == len(clip_data):
            cleanup_files()
            eprint('all clip processing failed')
            return jsonify({
                'ex': "\n".join([str(x) for x in clip_exception_store]),
                'msg': "processing all clips failed"
            })
    except Exception as ex:
        eprint('error in prediction')
        eprint(str(ex))
        cleanup_files()
        return jsonify({'ex': str(ex)})
    cleanup_files()
    model_hash = req_json['model_hash']
    eprint("checking model")
    if await APP_STATE.check_model_hash(model_hash):
        try:
            # audio-classifier code block
            song_class.genre_prediction = np.array(
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                dtype=np.float64
            )
            eprint("loading model")
            model = tf.keras.models.load_model("/".join([APP_STATE.model_dir, model_hash])+".h5")
            count = 0
            eprint('model loaded and beginning predictions')
            for image, features in zip(song_class.spectrograms, song_class.features):
                count += 1
                # get prediction for each clip and and calculate average
                image = np.array(image).reshape(classy.IMG_HEIGHT, classy.IMG_WIDTH, 1)
                features = np.array(features)
                eprint("running prediction")
                prediction = model.predict([np.array([features]), np.array([image])])
                song_class.genre_prediction += prediction[0]
            # calculate average of each clip prediction self
            song_class.genre_prediction = song_class.genre_prediction / count
            # log top-n genres to console
            eprint("running get_predictions")
            prediction_arr = song_class.get_predictions()
            # this should be refactored to be part of the api
            # as a parameter that can be passed
            # Log top n predictions to console
            n = 5
            top_n_genres = []
            top_n = np.argsort(prediction_arr)
            top_n = top_n[::-1][:n]
            eprint("converting predictions to text")
            for i, val in enumerate(top_n, start=1):
                top_n_genres.append(classy.LABELS_DICT[val])
            cleanup_files()
            eprint("|".join([str(x) for x in top_n_genres]))
            return jsonify({
                "predictions":"|".join([str(x) for x in top_n_genres])
            })
        except Exception as ex:
            eprint('error in model use attempt')
            eprint(str(ex))
            cleanup_files()
            return jsonify({
                'msg': 'model prediction caused an exception',
                'ex': str(ex)
            })
    else:
        eprint("model check failed, not found!")
        cleanup_files()
        return jsonify({
            'msg':'model not found'
        })
    cleanup_files()
    eprint('prediction request failed')
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
        eprint(str(ex))
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
