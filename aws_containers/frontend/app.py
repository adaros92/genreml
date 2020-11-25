import asyncio
import base64
import functools
import hashlib
import httpx
import itsdangerous
import json
import os
import re
import requests
import sys
import uuid
from quart import Quart, request, jsonify, abort, redirect, url_for, url_for, render_template
import dns.resolver as resolver
import numpy as np


app = Quart(__name__, static_folder='./static', static_url_path='/static')


class app_state:
    def __init__(self, loop):
        self.loop = loop
        self.signer = itsdangerous.Signer(os.environ['GENREML_SIGNING_TOKEN'])
        self.serializer = itsdangerous.Serializer(os.environ['GENREML_SIGNING_TOKEN'])
        self.filestore_directory = "/filestore"
        # generate endpoints
        self.predict_url = self.get_srv_record_url('GENREML_PREDICT_PORT', 'GENREML_PREDICT_ADDRESS', 'GENREML_PREDICT_SCHEMA')
        self.predict_node_url = self.get_srv_record_url('GENREML_PREDICT_NODE_PORT', 'GENREML_PREDICT_NODE_ADDRESS', 'GENREML_PREDICT_NODE_SCHEMA')
        self.spectro_url = self.get_srv_record_url('GENREML_SPECTRO_PORT', 'GENREML_SPECTRO_ADDRESS', 'GENREML_SPECTRO_SCHEMA')
        self.features_url = self.get_srv_record_url('GENREML_FEATURES_PORT', 'GENREML_FEATURES_ADDRESS', 'GENREML_FEATURES_SCHEMA')
        self.genres = os.environ['GENREML_GENRES'].split('|')
        self.model_hash = os.environ['GENREML_MODEL_HASH']
        self.image_labels_to_title = {
            "image_mel_spectrogram_grayscale_original": "Mel Spectrogram",
            "image_mel_spectrogram_image": "Mel Spectrogram",
            "image_mel_spectrogram_original_color": "Mel Spectrogram",
            "image_chromagram_grayscale_original": "Chromagram",
            "image_chromagram_image": "Chromagram",
            "image_chromagram_original_color": "Chromagram",
            "image_db_spectrogram_grayscale_original": "DB Spectrogram",
            "image_db_spectrogram_image": "DB Spectrogram",
            "image_db_spectrogram_original_color": "DB Spectrogram"
        }

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
            eprint("domain discovery failed")
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


@app.route('/uploadmultiple', methods=['POST'])
async def file_upload_handler():
    global APP_STATE
    # previous hard coded variables now from state class
    filestore_directory = APP_STATE.filestore_directory
    signer = APP_STATE.signer
    serializer = APP_STATE.serializer
    predict_node_url = APP_STATE.predict_node_url
    genres = APP_STATE.genres
    model_hash = APP_STATE.model_hash
    files = (await request.files).getlist("multiFileUploadForm")
    predictions = []
    reuse_api_call = False
    result = None
    for f in files:
        data = f.read()
        if type(data) == bytes:
            try:
                file_hash = hashlib.md5(data).hexdigest()
                song_upload = {
                    'ext': 'musicfile',
                    'data': base64.b64encode(data).decode('utf-8')
                }
                async with httpx.AsyncClient() as client:
                    spectro_tasks = {
                        'mel_spectrogram': APP_STATE.loop.create_task(client.post(APP_STATE.get_srv_record_url('GENREML_SPECTRO_PORT', 'GENREML_SPECTRO_ADDRESS', 'GENREML_SPECTRO_SCHEMA', False)+'/melspectrogram', data=serializer.dumps(song_upload), timeout=600.0)),
                        'chromagram': APP_STATE.loop.create_task(client.post(APP_STATE.get_srv_record_url('GENREML_SPECTRO_PORT', 'GENREML_SPECTRO_ADDRESS', 'GENREML_SPECTRO_SCHEMA', False)+'/chromagram', data=serializer.dumps(song_upload), timeout=600.0)),
                        'db_spectrogram': APP_STATE.loop.create_task(client.post(APP_STATE.get_srv_record_url('GENREML_SPECTRO_PORT', 'GENREML_SPECTRO_ADDRESS', 'GENREML_SPECTRO_SCHEMA', False)+'/dbspectrogram', data=serializer.dumps(song_upload), timeout=600.0))
                    }
                    song_upload['model_hash'] = model_hash
                    eprint("requesting prediction")
                    song_prediction = None
                    try:
                        song_prediction = await client.post(APP_STATE.get_srv_record_url('GENREML_PREDICT_PORT', 'GENREML_PREDICT_ADDRESS', 'GENREML_PREDICT_SCHEMA', False)+'/prediction', data=serializer.dumps(song_upload), timeout=600.0)
                    except Exception as ex:
                        eprint("prediction request failed")
                        eprint(str(ex))
                        pred = ["unknown"]
                        pass
                    eprint("pred:"+str(song_prediction))
                    try:
                        if song_prediction is not None:
                            song_prediction = song_prediction.json()
                            if "predictions" in song_prediction:
                                pred = song_prediction["predictions"].split("|")
                            if 'ex' in song_prediction:
                                pred = ["unknown"]
                                eprint("attempt to get prediction failed")
                                eprint(song_prediction['ex'])
                            if 'msg' in song_prediction:
                                eprint(song_prediction['msg'])
                    except Exception as ex:
                        eprint("prediction parse failed")
                        eprint(str(ex))
                        pass
                    eprint("building spectrograms")
                    result = {
                        "hash": file_hash,
                        "prediction": " ".join([str(x) for x in pred]),
                        "spectrogram": "",
                        "spectros": []
                    }
                    try:
                        spectrograms = {
                            'mel_spectrogram': await spectro_tasks['mel_spectrogram'],
                            'chromagram': await spectro_tasks['chromagram'],
                            'db_spectrogram': await spectro_tasks['db_spectrogram']
                        }
                        for item in spectrograms:
                            try:
                                spectrograms[item].raise_for_status()
                            except Exception as ex:
                                eprint(str(ex))
                                continue
                            if 'ex' not in spectrograms[item].json():
                                temp = spectrograms[item].json()
                                for spec_type in temp:
                                    image_label = "_".join(["image", item, spec_type])
                                    if not image_label.endswith('_original_color'):
                                        continue
                                    result["spectros"].append((
                                        APP_STATE.image_labels_to_title[image_label] if image_label in APP_STATE.image_labels_to_title else "Spectrogram",
                                        temp[spec_type]
                                    ))
                            else:
                                eprint(spectrograms[item].json()['ex'])
                    except Exception as ex:
                        eprint("attempt to get spectrograms failed")
                        eprint(str(ex))
                        pass
                    predictions.append(result)
            except Exception as ex:
                eprint("attempt to process file failed")
                eprint(str(ex))
                if result is not None:
                    predictions.append(result)
                else:
                    predictions.append({
                        "hash": file_hash,
                        "prediction": "unknown",
                        "spectros": []
                    })
        else:
            eprint("file wrong data type")
    if len(predictions) > 0:
        return await render_template('predictions.html', predictions=predictions)
    return redirect(url_for('index'))


@app.route('/')
async def index():
    """ Server route for the app's landing page """
    return await render_template('index.html')


# this deals with problem that sometimes
# async scheduler may not be "awake" and
# may not schedule some pending tasks.
# also we can put different state checks
# here and take action if state is bad
# or some type of internal state update
# must be performed
async def watcher():
    try:
        await asyncio.sleep(10)
    except Exception as ex:
        eprint(str(ex))
        pass


event_loop = None
APP_STATE = None
@app.before_serving
async def start():
    global event_loop
    global APP_STATE
    event_loop = asyncio.get_event_loop()
    APP_STATE = app_state(event_loop)
    event_loop.create_task(watcher())
    default_image = b'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'
    with open('/opt/static/favicon.png', 'wb') as f:
        f.write(base64.b64decode(default_image))
