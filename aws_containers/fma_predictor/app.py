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
import datetime


class app_state:
    def __init__(self, loop):
        self.loop = loop
        self.uid = str(uuid.uuid4())
        self.model_hash_registry = dict()
        self.model_dir = '/opt/model_store'
        self.temp_file_lock = asyncio.Lock()
        self.signer = itsdangerous.Signer(os.environ['SIGNING_TOKEN'])
        self.serializer = itsdangerous.Serializer(os.environ['SIGNING_TOKEN'])
        self.model_hash = os.environ['GENREML_MODEL_HASH']
        self.model_path = self.get_model_path(self.model_hash)
        if not self.check_model_hash(self.model_hash) is True:
            eprint("model not found during init")

    def get_model_path(self, model_hash):
        return "/".join([self.model_dir, model_hash])+".h5"

    def check_model_hash(self, model_hash):
        model_path = self.get_model_path(model_hash)
        return os.path.isfile(model_path)


def get_srv_record_url(port_key, address_key, schema_key, test_endpoint=True):
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
        eprint("exception in get srv record")
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


async def feature_spectrogram_uploads(work):
    global APP_STATE
    if 'work' not in work:
        return (None, dict(), dict(), dict())
    if 'item' not in work:
        return (None, dict(), dict(), dict())
    if work['work'] is False:
        return (None, dict(), dict(), dict())
    if work['item'] is None:
        return (None, dict(), dict(), dict())
    item = work['item']
    if 'ext' in work:
        ext = work['ext']
    else:
        ext = 'music_file'
    raw_data = base64.b64decode(item['data'])
    del(item['data'])
    del(work['item'])
    song_upload = {
        'ext': ext,
        'data': base64.b64encode(raw_data).decode('utf-8'),
    }
    async with httpx.AsyncClient() as client:
        features = APP_STATE.loop.create_task(client.post(get_srv_record_url('GENREML_FEATURES_PORT', 'GENREML_FEATURES_ADDRESS', 'GENREML_FEATURES_SCHEMA', False)+'/requestfeatures', data=APP_STATE.serializer.dumps(song_upload), timeout=600.0))
        spectrograms = APP_STATE.loop.create_task(client.post(get_srv_record_url('GENREML_SPECTRO_PORT', 'GENREML_SPECTRO_ADDRESS', 'GENREML_SPECTRO_SCHEMA', False)+'/melspectrogram', data=APP_STATE.serializer.dumps(song_upload), timeout=600.0))
        while features.done() is False or spectrograms.done() is False:
            await asyncio.sleep(0.2)
        features = await features
        spectrograms = await spectrograms
        try:
            spectrograms.raise_for_status()
            features.raise_for_status()
            features = features.json()
            if 'msg' in features:
                eprint(features['msg'])
            if 'ex' in features:
                eprint('problem with clip features request')
                eprint(features['ex'])
                return (False, dict(), dict(), dict())
            spectrograms = spectrograms.json()
            if 'msg' in spectrograms:
                eprint(spectrograms['ex'])
            if 'ex' in spectrograms:
                eprint('problem with clip spectrograms request')
                eprint(spectrograms['ex'])
                return (False, dict(), dict(), dict())
            spectrogram = base64.b64decode(spectrograms['image'])
            return (True, features, spectrogram, item, hashlib.md5(raw_data).hexdigest())
        except Exception as ex:
            eprint("failure in spectrogram and feature parsing after return from api calls")
            eprint(str(ex))
            return (False, dict(),dict(), dict())
    return (False, dict(), dict(), dict())


def get_uid():
    return str(uuid.uuid4()).replace('-', '')


def cleanup_files(cleanup_paths):
    for path in cleanup_paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception as ex:
            eprint("exception in cleanup files")
            eprint(str(ex))
            pass


async def run_model(model, processed):
    cleanup_paths = list()
    try:
        original_task = processed[3]
        song_class = classy.Song()
        features = processed[1]
        spectrogram = processed[2]
        #spectrogram = spectrogram['data']
        clip_hash = processed[-1]
        spectro_hash = hashlib.md5(spectrogram).hexdigest()
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
        #eprint("creating series")
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
        # audio-classifier code block
        song_class.genre_prediction = np.array(
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            dtype=np.float64
        )
        count = 0
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
        #eprint("running get_predictions")
        prediction_arr = song_class.get_predictions()
        # this should be refactored to be part of the api
        # as a parameter that can be passed
        # Log top n predictions to console
        n = 5
        top_n_genres = []
        top_n_pairs = []
        top_n = np.argsort(prediction_arr)
        top_n = top_n[::-1][:n]
        #eprint("converting predictions to text")
        for i, val in enumerate(top_n, start=1):
            top_n_genres.append(classy.LABELS_DICT[val])
            top_n_pairs.append([classy.LABELS_DICT[val],np.float64(val)])
        cleanup_files(cleanup_paths)
        #eprint("|".join([str(x) for x in top_n_genres]))
        pairs = []
        try:
            json.dumps(top_n_pairs)
            pairs = top_n_pairs
        except Exception as ex:
            eprint(ex)
            pass
        return {
            "predictor_id": APP_STATE.uid,
            "predictions": "|".join([str(x) for x in top_n_genres]),
            "prediction_clip_hash": clip_hash,
            "prediction_spectro_hash": spectro_hash,
            "prediction_pairs": pairs,
            **original_task
        }
    except Exception as ex:
        eprint('error in model use attempt')
        eprint(str(ex))
        cleanup_files(cleanup_paths)
        return None
    cleanup_files(cleanup_paths)
    return None


def log_feature_spectrogram_failures(processed):
    if processed[0] is None:
        return
    if processed[0] is False:
        eprint("features/spectrogram failure")
        if 'ex' in features:
            eprint("features failure")
            eprint(str(features['ex']))
            return
        if 'ex' in spectrogram:
            eprint("spectrogram failure")
            eprint(str(spectrogram['ex']))
            return


async def predictor(run_limit):
    global APP_STATE
    event_loop = APP_STATE.loop
    model = tf.keras.models.load_model(APP_STATE.model_path)
    if re.match("^[0-9]+$", run_limit) is None:
        return
    run_limit = int(run_limit)
    if run_limit <= 0:
        return
    for i in range(run_limit):
        async with httpx.AsyncClient() as client:
            try:
                work = await client.post(get_srv_record_url('GENREML_FRONTEND_PORT', 'GENREML_FRONTEND_ADDRESS', 'GENREML_FRONTEND_SCHEMA', False)+'/predictions', data=APP_STATE.signer.sign(APP_STATE.uid), timeout=60.0)
                work.raise_for_status()
                prep = await feature_spectrogram_uploads(work.json())
                try:
                    if prep[0] is True:
                        prediction = await run_model(model, prep)
                    else:
                        continue
                except Exception as ex:
                    eprint("failure in prediction attempt")
                    eprint(str(ex))
                    continue
                if prediction is not None:
                    async with httpx.AsyncClient() as client:
                        for i in range(5):
                            try:
                                send_back = await client.post(get_srv_record_url('GENREML_FRONTEND_PORT', 'GENREML_FRONTEND_ADDRESS', 'GENREML_FRONTEND_SCHEMA', False)+'/finishedpredictions', data=APP_STATE.serializer.dumps(prediction), timeout=60.0)
                                send_back.raise_for_status()
                                if send_back.json()['received'] is not True:
                                    continue
                                break
                            except Exception as ex:
                                eprint("error in posting prediction results")
                                eprint(str(ex))
                                continue
            except Exception as ex:
                eprint("error client call")
                eprint(str(ex))
                await asyncio.sleep(0.5)
                continue


async def check_before_exit():
    async with httpx.AsyncClient() as client:
        check = await client.post(get_srv_record_url('GENREML_FRONTEND_PORT', 'GENREML_FRONTEND_ADDRESS', 'GENREML_FRONTEND_SCHEMA', False)+'/predictsafetoreboot', data=APP_STATE.signer.sign(APP_STATE.uid), timeout=60.0)
        check = check.json()
        return check["safe"]


async def runner(run_limit):
    global APP_STATE
    event_loop = APP_STATE.loop
    model = tf.keras.models.load_model(APP_STATE.model_path)
    if re.match("^[0-9]+$", run_limit) is None:
        return
    run_limit = int(run_limit)
    if run_limit <= 0:
        return
    await predictor(str(run_limit))
    while await check_before_exit() is False:
        await predictor(str(run_limit))
    async with httpx.AsyncClient() as client:
        then = datetime.datetime.now()
        eprint("initiating restarts: "+then.isoformat())
        try:
            restart_features = await client.post(get_srv_record_url('GENREML_FEATURES_PORT', 'GENREML_FEATURES_ADDRESS', 'GENREML_FEATURES_SCHEMA', False)+'/restartsignal', data=APP_STATE.serializer.dumps({'restart':True}), timeout=5.0)
        except Exception as ex:
            eprint(str(ex))
            pass
        try:
            restart_spectrograms = await client.post(get_srv_record_url('GENREML_SPECTRO_PORT', 'GENREML_SPECTRO_ADDRESS', 'GENREML_SPECTRO_SCHEMA', False)+'/restartsignal', data=APP_STATE.serializer.dumps({'restart':True}), timeout=5.0)
        except Exception as ex:
            eprint(str(ex))
            pass
        eprint("restarts sent: "+str((then-datetime.datetime.now()).total_seconds()))


event_loop = asyncio.get_event_loop()
APP_STATE = app_state(event_loop)
health_check = False
while health_check is False:
    try:
        check = requests.get(get_srv_record_url('GENREML_FEATURES_PORT', 'GENREML_FEATURES_ADDRESS', 'GENREML_FEATURES_SCHEMA', False)+'/test', timeout=5.0)
        check.raise_for_status()
        health_check = True
    except Exception as ex:
        pass
health_check = False
while health_check is False:
    try:
        check = requests.get(get_srv_record_url('GENREML_SPECTRO_PORT', 'GENREML_SPECTRO_ADDRESS', 'GENREML_SPECTRO_SCHEMA', False)+'/test', timeout=5.0)
        check.raise_for_status()
        health_check = True
    except Exception as ex:
        pass
event_loop.run_until_complete(runner(os.environ['RUN_LIMIT']))
