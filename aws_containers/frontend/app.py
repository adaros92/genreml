import asyncio
import base64
import datetime
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
from quart import Quart, request, jsonify, abort, redirect, url_for, url_for, render_template, session
import dns.resolver as resolver
import numpy as np
import audio_classifier as classy
import aiofiles as aiof
from genreml.model.utils.file_handling import get_filetype, get_filename
import downloader


app = Quart(__name__, static_folder='./static', static_url_path='/static')
app.secret_key = str(uuid.uuid4())


class app_state:
    def __init__(self, loop):
        self.loop = loop
        self.signer = itsdangerous.Signer(os.environ['GENREML_SIGNING_TOKEN'])
        self.session_signer = itsdangerous.Signer(os.environ['SESSION_SIGNING_TOKEN'])
        self.serializer = itsdangerous.Serializer(os.environ['GENREML_SIGNING_TOKEN'])
        self.filestore_directory = "/opt/file_store"
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
        self.prediction_queue = asyncio.Queue()
        self.spectrograms_queue = asyncio.Queue()
        self.batch_store = dict()
        self.predictor_connections = dict()
        self.spectrogram_connections = dict()


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


def get_uid():
    return str(uuid.uuid4()).replace('-', '')


async def clean_up_file_later(path):
    return
    global APP_STATE
    try:
        TASK_LIMIT = 600
        then = datetime.datetime.now()
        await asyncio.sleep(TASK_LIMIT)
        if os.path.isfile(path):
            os.remove(path)
            eprint("deleted stale file: "+str(path))
        if (datetime.datetime.now()-then).total_seconds() < TASK_LIMIT:
            eprint("timer on file cleanup failed!")
    except Exception as ex:
        eprint("exception in stale task cleanup")
        eprint(str(ex))
        pass


async def create_clips(raw_data, bid, md5, model_hash, filename, name, ext, use_all=True, write_raw_data=True, passed_path=''):
    global APP_STATE
    return_state = True
    spectrogram_work_items = list()
    prediction_work_items = list()
    if bid not in APP_STATE.batch_store:
        return_state = False
        return (return_state, prediction_work_items, spectrogram_work_items)
    try:
        data_uid = get_uid()
        # previous hard coded variables now from state class
        filestore_directory = APP_STATE.filestore_directory
        upload_path = filestore_directory+"/"+data_uid+'.'+ext
        if write_raw_data:
            async with aiof.open(upload_path, 'wb') as f:
                await f.write(raw_data)
        else:
            upload_path = passed_path
        if not os.path.isfile(upload_path):
            raise Exception("could not write data in create_clips or youtube file does not exist")
        eprint("defining class")
        song_class = classy.Song()
        song_class.path = upload_path
        eprint("extracting song data")
        song_class.extract_song_data()
        eprint("starting clips")
        if use_all is False:
            song_class.clips = [song_class.clips[0]]
        clip_count = 0
        for clip in song_class.clips:
            clip_count += 1
            try:
                uid = get_uid()
                # export wav file
                scaled = np.int16(clip / np.max(np.abs(clip)) * 32767)
                if clip_count == 1:
                    classy.write('/opt/clip_store/'+uid+'.'+'wav', song_class.sr, scaled)
                    clip_item = {
                        'path': '/opt/clip_store/'+uid+'.'+'wav',
                        'filename': uid+'.'+'wav',
                        'ext': 'wav',
                        'uid': uid,
                        'batch_id': bid,
                        'source_md5': md5,
                        'model_hash': model_hash,
                        'result': None
                    }
                    APP_STATE.batch_store[bid]['play_clips'][uid] = clip_item
                    APP_STATE.loop.create_task(clean_up_file_later('/opt/clip_store/'+uid+'.'+'wav'))
                classy.write('/opt/prediction_store/'+uid+'.'+'wav', song_class.sr, scaled)
                prediction_work_item = {
                    'path': '/opt/prediction_store/'+uid+'.'+'wav',
                    'filename': uid+'.'+'wav',
                    'ext': 'wav',
                    'uid': uid,
                    'batch_id': bid,
                    'source_md5': md5,
                    'model_hash': model_hash,
                    'result': None
                }
                prediction_work_items.append(prediction_work_item)
                APP_STATE.batch_store[bid]['predictions'][uid] = prediction_work_item
                await APP_STATE.prediction_queue.put(prediction_work_item)
                APP_STATE.loop.create_task(clean_up_file_later('/opt/prediction_store/'+uid+'.'+'wav'))
                eprint("prediction in the queue")
                classy.write('/opt/spectrogram_store/'+uid+'.'+'wav', song_class.sr, scaled)
                spectrogram_work_item = {
                    'path': '/opt/spectrogram_store/'+uid+'.'+'wav',
                    'filename': uid+'.'+'wav',
                    'ext': 'wav',
                    'uid': uid,
                    'batch_id': bid,
                    'source_md5': md5,
                    'model_hash': model_hash,
                    'images': None
                }
                spectrogram_work_items.append(spectrogram_work_item)
                APP_STATE.batch_store[bid]['spectrograms'][uid] = spectrogram_work_item
                await APP_STATE.spectrograms_queue.put(spectrogram_work_item)
                APP_STATE.loop.create_task(clean_up_file_later('/opt/spectrogram_store/'+uid+'.'+'wav'))
                eprint("spectrogram in the queue")
            except Exception as ex:
                eprint("failure in clip processing")
                eprint(str(ex))
                pass
    except Exception as ex:
        eprint("failure in music file processing")
        eprint(str(ex))
        return_state = False
        pass
    try:
        if os.path.isfile(upload_path):
            os.remove(upload_path)
    except Exception as ex:
        eprint(str(ex))
        pass
    return (return_state, prediction_work_items, spectrogram_work_items)


async def clean_up_task_later(batch_id):
    global APP_STATE
    try:
        TASK_LIMIT = 600
        then = datetime.datetime.now()
        await asyncio.sleep(TASK_LIMIT)
        if batch_id not in APP_STATE.batch_store:
            return
        if 'time' in APP_STATE.batch_store[batch_id]:
            then = APP_STATE.batch_store[batch_id]['time']
        if len(APP_STATE.batch_store[batch_id]['predictions'].keys()) == 0 and len(APP_STATE.batch_store[batch_id]['spectrograms'].keys()) == 0:
            if (datetime.datetime.now()-then).total_seconds() >= TASK_LIMIT:
                eprint("deleted stale task: "+str(batch_id))
            del(APP_STATE.batch_store[batch_id])
        if batch_id not in APP_STATE.batch_store:
            return
        if (datetime.datetime.now()-then).total_seconds() < TASK_LIMIT:
            eprint("timer on task cleanup failed!")            
        if (datetime.datetime.now()-then).total_seconds() >= TASK_LIMIT:
            del(APP_STATE.batch_store[batch_id])
            eprint("deleted stale task: "+str(batch_id))
    except Exception as ex:
        eprint("exception in stale task cleanup")
        eprint(str(ex))
        pass


@app.route('/download_youtube', methods=['POST'])
async def process_youtube_video():
    global APP_STATE
    batch_id = session.get('batchid')
    eprint("work request incoming")
    if APP_STATE.session_signer.validate(batch_id) is not True:
        eprint("bad batch id")
        return redirect(url_for('index'))
    else:
        batch_id = APP_STATE.session_signer.unsign(batch_id).decode('utf-8')
        eprint(str(batch_id))
        APP_STATE.batch_store[batch_id] = {
            'batch_id': batch_id,
            'time': datetime.datetime.now(),
            'predictions': dict(),
            'spectrograms': dict(),
            'play_clips': dict(),
            'model_hash': APP_STATE.model_hash
        }
        APP_STATE.loop.create_task(clean_up_task_later(batch_id))
    background_work = []
    """ Route for downloading a Youtube video and performing feature extraction + prediction """
    try:
        filestore_directory = APP_STATE.filestore_directory
        # Get the Youtube link from the request
        youtube_url = (await request.form)['text']
        # Only process results if valid youtube video link
        if "youtube" in youtube_url and youtube_url[:8] == "https://" and "v=" in youtube_url:
            filepath = downloader.download_link(youtube_url, directory_path=filestore_directory)
            async with aiof.open(filepath, 'rb') as f:
                raw_data = await f.read()
            file_hash = hashlib.md5(raw_data).hexdigest()
            start_work = await create_clips(raw_data, batch_id, file_hash, APP_STATE.model_hash, filepath.split('/')[-1], filepath.split('/')[-1].split('.')[0], filepath.split('/')[-1].split('.')[-1], False, False, filepath)
            background_work.append({
                'md5': file_hash,
                'work': start_work,
                'filename': filepath.split('/')[-1]
            })
    except Exception as ex:
        eprint("error in youtube dl endpoint")
        eprint(str(ex))
        pass
    try:
        if len(background_work) > 0:
            view_items = await render_prediction_view(background_work)
            return await render_template('predictions.html', genre_ml_data={
                'batch_id': batch_id,
                'view_data': view_items
            })          
    except Exception as ex:
        eprint("error rendering view")
        eprint(str(ex))
        return redirect(url_for('index'))
    return redirect(url_for('index'))


async def render_prediction_view(background_work):
    view_items = []
    for item in background_work:
        try:
            view_item = {
                'md5': item['md5'],
                'filename': item['filename'],
                'spectro_uids': list(),
                'predict_uids': list()
            }
            if item['md5'] != 'unknown':
                view_item['msg'] = 'Please wait while we are getting your results in the background.'
            else:
                view_item['msg'] = 'Something went wrong, please try again or use a different file.'
            if len(item['work']) < 3:
                view_items.append(view_item)
                continue
            spectrogram_work_items = item['work'][2]
            prediction_work_items = item['work'][1]
            for spectro in spectrogram_work_items:
                if 'uid' in spectro:
                    view_item['spectro_uids'].append({
                        'uid': spectro['uid'],
                        'value': '',
                        'ready': False
                    })
            for predict in prediction_work_items:
                if 'uid' in predict:
                    view_item['predict_uids'].append({
                        'uid': predict['uid'],
                        'value': '',
                        'ready': False
                    })
            view_items.append(view_item)
        except Exception as ex:
            eprint("error rendering view")
            eprint(str(ex))
            continue
    if len(view_items) > 0:
        return view_items
    else:
        raise Exception("No view generated. render_prediction_view generated view of 0 items")


@app.route('/uploads', methods=['POST'])
async def file_upload_handler():
    global APP_STATE
    batch_id = session.get('batchid')
    eprint("work request incoming")
    if APP_STATE.session_signer.validate(batch_id) is not True:
        eprint("bad batch id")
        return redirect(url_for('index'))
    else:
        batch_id = APP_STATE.session_signer.unsign(batch_id).decode('utf-8')
        eprint(str(batch_id))
        APP_STATE.batch_store[batch_id] = {
            'batch_id': batch_id,
            'time': datetime.datetime.now(),
            'predictions': dict(),
            'spectrograms': dict(),
            'play_clips': dict(),
            'model_hash': APP_STATE.model_hash
        }
    APP_STATE.loop.create_task(clean_up_task_later(batch_id))
    files = (await request.files).getlist("fileUploadForm")
    background_work = []
    for f in files:
        data = f.read()
        if type(data) == bytes:
            try:
                file_hash = hashlib.md5(data).hexdigest()
                try:
                    filename = f.filename
                    eprint(str(filename))
                    name = filename.split('.')[0]
                    ext = filename.split('.')[-1]
                    if name == ext:
                        ext = 'music_file'
                    start_work = await create_clips(data, batch_id, file_hash, APP_STATE.model_hash, filename, name, ext, False)
                    background_work.append({
                        'md5': file_hash,
                        'work': start_work,
                        'filename': filename
                    })
                except Exception as ex:
                    background_work.append({
                        'md5': file_hash,
                        'work': tuple()
                    })
                    pass
            except Exception as ex:
                eprint("attempt to process file failed")
                eprint(str(ex))
                background_work.append({
                    'md5': "unknown",
                    'work': tuple()
                })
        else:
            eprint("file wrong data type")
    # (return_state, prediction_work_items, spectrogram_work_items)
    try:
        view_items = await render_prediction_view(background_work)
        return await render_template('predictions.html', genre_ml_data={
            'batch_id': batch_id,
            'view_data': view_items
        })
    except Exception as ex:
        eprint("error rendering view")
        eprint(str(ex))
        return redirect(url_for('index'))
    return redirect(url_for('index'))


async def long_poll_queuer(queue):
    then = datetime.datetime.now()
    while (datetime.datetime.now()-then).total_seconds() < 30:
        if not queue.empty():
            return {
                'work': True,
                'item': await queue.get()
            }
        await asyncio.sleep(0.3)
    return {'work': False, 'item': None}


async def prep_queue_item(data):
    if data['item'] is None:
        return jsonify(data)
    if 'path' not in data['item']:
        return jsonify(data)
    if not os.path.isfile(data['item']['path']):
        return jsonify(data)
    async with aiof.open(data['item']['path'], 'rb') as f:
        data['item']['data'] = base64.b64encode(await f.read()).decode('utf-8')
    send_back = jsonify(data)
    del(data['item']['data'])
    eprint("queue work prepped")
    return send_back


@app.route('/predictions', methods=['POST'])
async def get_prediction_work():
    global APP_STATE
    predictor_id = None
    #eprint("incoming prediction request")
    req_data = await request.get_data()
    try:
        if APP_STATE.signer.validate(req_data):
            #eprint("validated prediction request")
            predictor_id = APP_STATE.signer.unsign(req_data).decode('utf-8')
            APP_STATE.predictor_connections[predictor_id] = True
            data = await long_poll_queuer(APP_STATE.prediction_queue)
            del(APP_STATE.predictor_connections[predictor_id])
            return await prep_queue_item(data)
    except Exception as ex:
        eprint("error when prepping prediction queue")
        eprint(str(ex))
        if predictor_id is not None:
            if predictor_id in APP_STATE.predictor_connections:
                del(APP_STATE.predictor_connections[predictor_id])
        return jsonify({
            'msg': 'could not send item',
            'ex': str(ex),
            'work': False,
            'item': None
        })
    return jsonify({
        'work': False,
        'item': None
    })


@app.route('/predictsafetoreboot', methods=['POST'])
async def predict_safe_to_reboot():
    req_data = await request.get_data()
    if APP_STATE.signer.validate(req_data):
        #eprint("validated prediction request")
        predictor_id = APP_STATE.signer.unsign(req_data).decode('utf-8')
        if predictor_id in APP_STATE.predictor_connections:
            del(APP_STATE.predictor_connections[predictor_id])
    if len(APP_STATE.predictor_connections.keys()) > 0:
        return jsonify({"safe": True})
    return jsonify({"safe": False})


@app.route('/spectrogramsafetoreboot', methods=['POST'])
async def spectrogram_safe_to_reboot():
    req_data = await request.get_data()
    if APP_STATE.signer.validate(req_data):
        #eprint("validated prediction request")
        spectrogram_id = APP_STATE.signer.unsign(req_data).decode('utf-8')
        if spectrogram_id in APP_STATE.spectrogram_connections:
            del(APP_STATE.spectrogram_connections[spectrogram_id])
    if len(APP_STATE.spectrogram_connections.keys()) > 0:
        return jsonify({"safe": True})
    return jsonify({"safe": False})


@app.route('/spectrograms', methods=['POST'])
async def get_spectrogram_work():
    global APP_STATE
    spectrogram_id = None
    #eprint("incoming spectrogram request")
    req_data = await request.get_data()
    try:
        if APP_STATE.signer.validate(req_data):
            #eprint("validated spectrogram request")
            spectrogram_id = APP_STATE.signer.unsign(req_data).decode('utf-8')
            APP_STATE.spectrogram_connections[spectrogram_id] = True
            data = await long_poll_queuer(APP_STATE.spectrograms_queue)
            del(APP_STATE.spectrogram_connections[spectrogram_id])
            return await prep_queue_item(data)
    except Exception as ex:
        eprint("error when prepping predispectrogram queue")
        eprint(str(ex))
        if spectrogram_id is not None:
            if spectrogram_id in APP_STATE.spectrogram_connections:
                del(APP_STATE.spectrogram_connections[spectrogram_id])
        return jsonify({
            'msg': 'payload did not have valid signature',
            'ex': str(ex),
            'work': False,
            'item': None
        })
    return jsonify({
        'work': False,
        'item': None
    })


# {
#     'path': '/opt/spectrogram_store/'+uid+'.'+'music_file',
#     'uid': uid,
#     'batch_id': bid,
#     'source_md5': md5,
#     'model_hash': model_hash,
#     'result': None
# }
@app.route('/finishedspectrograms', methods=['POST'])
async def post_spectrograms():
    global APP_STATE
    req_data = await request.get_data()
    try:
        req_json = APP_STATE.serializer.loads(req_data)
        if req_json['batch_id'] in APP_STATE.batch_store and req_json['uid'] in APP_STATE.batch_store[req_json['batch_id']]['spectrograms']:
            eprint("spectrogram result from batch id: "+req_json["batch_id"])
            APP_STATE.batch_store[req_json['batch_id']]['spectrograms'][req_json['uid']]['images'] = req_json
            try:
                if os.path.isfile(APP_STATE.batch_store[req_json['batch_id']]['spectrograms'][req_json['uid']]['path']):
                    os.remove(APP_STATE.batch_store[req_json['batch_id']]['spectrograms'][req_json['uid']]['path'])
            except Exception as ex:
                eprint(str(ex))
                pass
        return jsonify({
            'received': True
        })
    except Exception as ex:
        eprint("issue with finished spectrogram post")
        eprint(str(ex))
        return jsonify({
            'msg': 'payload did not have valid signature',
            'ex': str(ex),
            'received': False
        })
    return jsonify({
        'received': True
    })


@app.route('/finishedpredictions', methods=['POST'])
async def post_predictions():
    global APP_STATE
    req_data = await request.get_data()
    try:
        req_json = APP_STATE.serializer.loads(req_data)
        if 'predictor_id' in req_json and 'predictions' in req_json:
            eprint(" ".join(["container", req_json['predictor_id'], "predicted", req_json['predictions']]))
            if req_json['batch_id'] in APP_STATE.batch_store and req_json['uid'] in APP_STATE.batch_store[req_json['batch_id']]['predictions']:
                eprint("prediction result from batch id: "+req_json["batch_id"])
                # {
                #     'predictor_id': 'ffee4940-6ec3-4952-bcc2-af7bc99a4928',
                #     'predictions': 'Hip-Hop|Electronic|Pop|Punk|Rock',
                #     'batch_id': 'e00e787e-597d-4178-b9d7-a885a9c8ba86',
                #     'ext': 'wav',
                #     'filename': '84a655b173a84071b09f9e3cc5d4a683.wav',
                #     'model_hash': '68b1d64e0635f36d1a71d1b2c7000a69b6d02dcccfaa9893408f93fe603faf39',
                #     'path': '/opt/prediction_store/84a655b173a84071b09f9e3cc5d4a683.wav',
                #     'result': None,
                #     'source_md5': '72e8250037da01f3b3695b3617ae1dd7',
                #     'uid': '84a655b173a84071b09f9e3cc5d4a683'
                # }
                APP_STATE.batch_store[req_json['batch_id']]['predictions'][req_json['uid']]['result'] = {x:req_json[x] for x in req_json if x.startswith('predict')}
                try:
                    if os.path.isfile(APP_STATE.batch_store[req_json['batch_id']]['predictions'][req_json['uid']]['path']):
                        os.remove(APP_STATE.batch_store[req_json['batch_id']]['predictions'][req_json['uid']]['path'])
                except Exception as ex:
                    eprint(str(ex))
                    pass
        return jsonify({
            'received': True
        })
    except Exception as ex:
        eprint(str(ex))
        return jsonify({
            'msg': 'payload did not have valid signature',
            'ex': str(ex),
            'received': False
        })
    return jsonify({
        'received': True
    })


@app.route('/getpredictionbyuid/<uid>', methods=['GET'])
async def get_prediction_by_uid(uid):
    global APP_STATE
    try:
        then = datetime.datetime.now()
        batch_id = session.get('batchid')
        if APP_STATE.session_signer.validate(batch_id) is not True:
            return jsonify({
                'msg': 'batch id not validated',
                'batch_id': batch_id,
                'uid': uid,
                'ready': False,
                'prediction': None
            })
        else:
            batch_id = APP_STATE.session_signer.unsign(batch_id).decode('utf-8')
        while batch_id not in APP_STATE.batch_store and (datetime.datetime.now() - then).total_seconds() < 15:
            await asyncio.sleep(0.3)
        if batch_id not in APP_STATE.batch_store:
            return jsonify({
                'msg': 'batch id not found',
                'batch_id': batch_id,
                'uid': uid,
                'ready': False,
                'prediction': None
            })
        while 'predictions' not in APP_STATE.batch_store[batch_id] and (datetime.datetime.now() - then).total_seconds() < 15:
            await asyncio.sleep(0.3)
        if 'predictions' not in APP_STATE.batch_store[batch_id]:
            return jsonify({
                'msg': 'predictions not found in data store',
                'batch_id': batch_id,
                'uid': uid,
                'ready': False,
                'prediction': None
            })
        while uid not in APP_STATE.batch_store[batch_id]['predictions'] and (datetime.datetime.now() - then).total_seconds() < 15:
            await asyncio.sleep(0.3)
        if uid not in APP_STATE.batch_store[batch_id]['predictions']:
            return jsonify({
                'msg': 'uid not found',
                'batch_id': batch_id,
                'uid': uid,
                'ready': False,
                'prediction': None
            })
        while APP_STATE.batch_store[batch_id]['predictions'][uid]['result'] is None and (datetime.datetime.now() - then).total_seconds() < 15:
            await asyncio.sleep(0.3)
        if APP_STATE.batch_store[batch_id]['predictions'][uid]['result'] is None:
            return jsonify({
                'batch_id': batch_id,
                'uid': uid,
                'ready': False,
                'prediction': None
            })
        else:
            return_value = APP_STATE.batch_store[batch_id]['predictions'][uid]['result']
            del(APP_STATE.batch_store[batch_id]['predictions'][uid])
            return jsonify({
                'batch_id': batch_id,
                'uid': uid,
                'ready': True,
                'prediction': return_value
            })
    except Exception as ex:
        eprint("attempt to get prediction results failed")
        eprint(str(ex))
        return jsonify({
            'msg': 'something went wrong',
            'ex': str(ex)
        })
    return jsonify({
        'msg': 'something went wrong'
    })


@app.route('/getspectrogramsbyuid/<uid>', methods=['GET'])
async def get_spectrograms_by_uid(uid):
    global APP_STATE
    try:
        then = datetime.datetime.now()
        batch_id = session.get('batchid')
        if APP_STATE.session_signer.validate(batch_id) is not True:
            return jsonify({
                'msg': 'batch id not validated',
                'batch_id': batch_id,
                'uid': uid,
                'ready': False,
                'images': None
            })
        else:
            batch_id = APP_STATE.session_signer.unsign(batch_id).decode('utf-8')
        while batch_id not in APP_STATE.batch_store and (datetime.datetime.now() - then).total_seconds() < 15:
            await asyncio.sleep(0.3)
        if batch_id not in APP_STATE.batch_store:
            return jsonify({
                'msg': 'batch id not found',
                'batch_id': batch_id,
                'uid': uid,
                'ready': False,
                'images': None
            })
        while 'spectrograms' not in APP_STATE.batch_store[batch_id] and (datetime.datetime.now() - then).total_seconds() < 15:
            await asyncio.sleep(0.3)
        if 'spectrograms' not in APP_STATE.batch_store[batch_id]:
            return jsonify({
                'msg': 'spectrograms not found in data store',
                'batch_id': batch_id,
                'uid': uid,
                'ready': False,
                'images': None
            })
        while uid not in APP_STATE.batch_store[batch_id]['spectrograms'] and (datetime.datetime.now() - then).total_seconds() < 15:
            await asyncio.sleep(0.3)
        if uid not in APP_STATE.batch_store[batch_id]['spectrograms']:
            return jsonify({
                'msg': 'uid not found',
                'batch_id': batch_id,
                'uid': uid,
                'ready': False,
                'images': None
            })
        while APP_STATE.batch_store[batch_id]['spectrograms'][uid]['images'] is None and (datetime.datetime.now() - then).total_seconds() < 15:
            await asyncio.sleep(0.3)
        if APP_STATE.batch_store[batch_id]['spectrograms'][uid]['images'] is None:
            return jsonify({
                'batch_id': batch_id,
                'uid': uid,
                'ready': False,
                'images': None
            })
        else:
            return_value = APP_STATE.batch_store[batch_id]['spectrograms'][uid]['images']
            del(APP_STATE.batch_store[batch_id]['spectrograms'][uid])
            return jsonify({
                'batch_id': batch_id,
                'uid': uid,
                'ready': True,
                'images': return_value
            })
    except Exception as ex:
        eprint("attempt to get spectrogram results failed")
        eprint(str(ex))
        return jsonify({
            'msg': 'something went wrong',
            'ex': str(ex)
        })
    return jsonify({
        'msg': 'something went wrong'
    })


# this route and method is dirty, it will hold the connection until it times out
# or it will return what is being requested. It shouldn't be a problem but 
# it was expediently coded
@app.route('/getaclip', methods=['GET'])
async def get_a_clip():
    global APP_STATE
    try:
        then = datetime.datetime.now()
        batch_id = session.get('batchid')
        if APP_STATE.session_signer.validate(batch_id) is not True:
            return jsonify({
                'msg': 'batch id not validated',
                'batch_id': batch_id,
                'ready': False,
                'sample': None
            })
        else:
            batch_id = APP_STATE.session_signer.unsign(batch_id).decode('utf-8')
        while 'play_clips' not in APP_STATE.batch_store[batch_id]:
            await asyncio.sleep(0.3)
        while len(APP_STATE.batch_store[batch_id]['play_clips'].values()) == 0:
            await asyncio.sleep(0.3)
        for item in APP_STATE.batch_store[batch_id]['play_clips'].values():
            if 'path' in item:
                clip = item
                if os.path.isfile(clip['path']):
                    clip['ready'] = True
                    async with aiof.open(clip['path'], 'rb') as f:
                        clip['sample'] = base64.b64encode(await f.read()).decode('utf-8')
                    os.remove(clip['path'])
                    return jsonify(clip)
        return jsonify({
            'msg': 'sample does not exist',
            'ready': False,
            'sample': None
        })
    except Exception as ex:
        eprint("attempt to get sample failed")
        eprint(str(ex))
        return jsonify({
            'msg': 'something went wrong',
            'ex': str(ex),
            'ready': False,
            'sample': None
        })
    return jsonify({
        'msg': 'something went wrong',
        'ready': False,
        'sample': None
    })


@app.route('/')
async def index():
    global APP_STATE
    batch_id = str(uuid.uuid4())
    #eprint("batch id: "+batch_id)
    session['batchid'] = APP_STATE.session_signer.sign(batch_id).decode('utf-8')
    """ Server route for the app's landing page """
    return await render_template('index.html', genre_ml_data={
        'batch_id': batch_id
    })


@app.route('/about')
async def about():
    global APP_STATE
    batch_id = str(uuid.uuid4())
    #eprint("batch id: "+batch_id)
    session['batchid'] = APP_STATE.session_signer.sign(batch_id).decode('utf-8')
    """ Server route for the app's landing page """
    return await render_template('about.html', genre_ml_data={
        'batch_id': batch_id
    })


@app.route('/contacts')
async def contacts():
    global APP_STATE
    batch_id = str(uuid.uuid4())
    #eprint("batch id: "+batch_id)
    session['batchid'] = APP_STATE.session_signer.sign(batch_id).decode('utf-8')
    """ Server route for the app's landing page """
    return await render_template('contacts.html', genre_ml_data={
        'batch_id': batch_id
    })


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
