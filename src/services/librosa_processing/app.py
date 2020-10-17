from quart import Quart, request, jsonify, abort
import aiohttp
import asyncio
import base64
import json
import librosa
import numpy as np
import uuid
import zlib


app = Quart(__name__)
event_loop = asyncio.get_event_loop()


# common pattern illustrated in https://stackoverflow.com/questions/56766072/post-method-to-upload-file-with-json-object-in-python-flask-app
# librosa processing code adapted from https://github.com/kumargauravsingh14/music-genre-classification/blob/master/Music%20Genre%20Classification.py
@app.route('/sampleprocessor',methods=['POST'])
def librosa_process():
    uploaded_file = request.files['sample']
    json_request = json.load(request.files['json'])
    headers = None
    if 'headers' in json_request:
        headers = json_request['headers']
    to_dict = False
    if 'to_dict' in json_request:
        to_dict = json_request['to_dict']
    audio_file_length = json_request["length"]
    sample_seconds = json_request["sample_seconds"]
    return_data = []
    errors = []
    if audio_file_length/sample_seconds > 1.0:
        for section in range(int(audio_file_length/sample_seconds)):
            try:
                error = None
                y, sr = librosa.load(songname, mono=True, offset=sample_seconds*section, duration=sample_seconds)
            except Exception as ex:
                errors.apepnd(ex)
                print("Bad filename: "+filename)
                break
            chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
            #rmse = librosa.feature.rmse(y=y)
            rmse = librosa.feature.rms(y=y)[0]
            spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)
            spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
            rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            zcr = librosa.feature.zero_crossing_rate(y)
            mfcc = librosa.feature.mfcc(y=y, sr=sr)
            return_data = return_data + [np.mean(chroma_stft), np.mean(rmse), np.mean(spec_cent), np.mean(spec_bw), np.mean(rolloff), np.mean(zcr)]
            for e in mfcc:
                return_data.append(np.mean(e))
    if to_dict is True and headers is not None and len(headers) == len(data):
        return jsonify({
            'object': {headers[i]: data[i] for i in range(len(headers))},
            'errors': errors
        })
    return jsonify({
        'array': return_data,
        'errors': errors
    })
