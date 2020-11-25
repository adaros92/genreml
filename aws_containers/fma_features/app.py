from quart import Quart, request, jsonify, abort, redirect, url_for
import asyncio
import base64
import hashlib
import io
import itsdangerous
import json
import librosa
import numpy as np
import os
import pandas as pd
import pprint
import re
import sys
from genreml.model.processing.audio import AudioFile
from genreml.model.processing.audio_features import SpectrogramGenerator
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import audio_classifier as classy


app = Quart(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024


class app_state:
    def __init__(self, loop):
        self.loop = loop
        self.signer = itsdangerous.Signer(os.environ['SIGNING_TOKEN'])
        self.serializer = itsdangerous.Serializer(os.environ['SIGNING_TOKEN'])


# simple logging snippet from https://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, flush=True, **kwargs)


@app.route('/test',methods=['GET'])
async def test_server():
    return jsonify({'msg': 'server up'})


async def get_features(file_location):
    try:
        # af extraction
        audio_signal, sample_rate = librosa.load(file_location)
        song_class = classy.Song()
        ds = song_class._Song__get_features(audio_signal, sample_rate)
        return (True, ds.to_json())
    except Exception as ex:
        eprint("feature extraction failed")
        eprint(str(ex))
        return (False, ex)


@app.route('/requestfeatures', methods=['POST'])
async def generate_features():
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
    req_data = await request.get_data()
    try:
        req_json = APP_STATE.serializer.loads(req_data)
    except Exception as ex:
        eprint(str(ex))
        cleanup_files()
        return jsonify({
            'msg': 'payload did not have valid signature',
            'ex': str(ex)
            })
    if 'data' in req_json and 'ext' in req_json:
        data = req_json['data']
        # this will be audio
        try:
            raw_data = base64.b64decode(data)
            data_hash = hashlib.sha256(raw_data).hexdigest()
            upload_path = data_hash+'.'+req_json['ext']
            with open(upload_path, 'wb') as f:
                f.write(raw_data)
            cleanup_paths.append(upload_path)
            features = await get_features(upload_path)
            if features[0] is True:
                return_data = features[1]
                cleanup_files()
                return return_data
            else:
                eprint(str(features[1]))
                eprint('feature extraction failed')
                return_data = {
                    'msg': 'feature extraction failed',
                    'ex': str(features[1])
                }
        except Exception as ex:
            eprint(str(ex))
            return_data = {
                'msg': 'feature extraction failed',
                'ex': str(ex)
            }
            pass
        cleanup_files()
        return jsonify(return_data)
    cleanup_files()
    return jsonify({'msg':'something went wrong'})


event_loop = None
APP_STATE = None
@app.before_serving
async def start():
    global event_loop
    global APP_STATE
    event_loop = asyncio.get_event_loop()
    APP_STATE = app_state(event_loop)
