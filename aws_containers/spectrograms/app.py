import asyncio
import base64
import hashlib
import io
import itsdangerous
import json
import librosa
import os
import re
import sys
import uuid
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import pandas as pd
from genreml.model.processing.audio import AudioFile
from genreml.model.processing.audio_features import SpectrogramGenerator
from PIL import Image
from quart import Quart, request, jsonify, abort, redirect, url_for
import aiofiles as aiof
import datetime
import httpx
import dns.resolver as resolver


app = Quart(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024


class app_state:
    def __init__(self, loop):
        self.loop = loop
        self.signer = itsdangerous.Signer(os.environ['GENREML_SIGNING_TOKEN'])
        self.serializer = itsdangerous.Serializer(os.environ['GENREML_SIGNING_TOKEN'])
        self.uid = str(uuid.uuid4())


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


@app.route('/test',methods=['GET'])
async def test_server():
    return jsonify({'msg': 'server up'})


async def gen_spectrogram(raw_data, file_location, spectro_type="melspectrogram"):
    MIN_CLIP_LENGTH = 29
    cleanup_paths = []
    images = {}
    file_uid = str(uuid.uuid4())
    audio_signal, sample_rate = librosa.load(file_location)
    # length of song in seconds
    length = len(audio_signal) / sample_rate
    # assert song length greater than or equal to minimum
    if length >= MIN_CLIP_LENGTH:
        clip_index = int(sample_rate * MIN_CLIP_LENGTH)
        audio_signal = audio_signal[:clip_index]
    spectrogram = SpectrogramGenerator(audio_signal, sample_rate)
    # spectrogram
    if spectro_type == "melspectrogram":
        spectrogram.spectrogram_type = "melspectrogram"
        mel_spect = spectrogram._create_db_melspectrogram_data(spectrogram.audio_signal, spectrogram.sample_rate)
        norm_mel_spect = spectrogram.normalize(mel_spect)
        eight_bit_spectrogram = spectrogram.convert_pixels_to_8_bits(norm_mel_spect)
        final_spectrogram = spectrogram.flip_and_invert(eight_bit_spectrogram)
    elif spectro_type == "chromagram":
        spectrogram.spectrogram_type = "chromagram"
        chroma_spect = spectrogram._create_chromagram_data(spectrogram.audio_signal, spectrogram.sample_rate)
        final_spectrogram = chroma_spect
    elif spectro_type == "dbspectrogram":
        spectrogram.spectrogram_type = "dbspectrogram"
        db_spect = spectrogram._create_db_spectrogram_data(spectrogram.audio_signal)
        final_spectrogram = db_spect
    else:
        return await gen_spectrogram(raw_data, file_location, "melspectrogram")
    # matplot 1
    fig = plt.figure(frameon=False)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    # save file 1
    temp = ax.imshow(final_spectrogram, aspect='auto', cmap='Greys')
    fig.savefig(file_uid+'_g'+'.png')
    cleanup_paths.append(file_uid+'_g'+'.png')
    plt.close(fig)
    # matplot 2
    fig2 = plt.figure(frameon=False)
    ax2 = plt.Axes(fig2, [0., 0., 1., 1.])
    ax2.set_axis_off()
    fig2.add_axes(ax2)
    # save file 2
    temp2 = ax2.imshow(final_spectrogram, aspect='auto')
    fig2.savefig(file_uid+'_c'+'.png')
    cleanup_paths.append(file_uid+'_c'+'.png')
    plt.close(fig2)
    # shape image for NN
    dest = file_uid+'_g'+'.png'
    img_width = 335
    img_height = 200
    img = Image.open(dest).convert('L')
    img = img.crop((55, 50, 390, 250))
    img = img.resize((img_width, img_height))
    img.save(file_uid+'_input'+'.png')
    cleanup_paths.append(file_uid+'_input'+'.png')
    img_array = np.array(img, dtype=np.float32)
    # refactor with aio files later
    async with aiof.open(file_uid+'_g'+'.png', 'rb') as gray:
        images['grayscale_original'] = base64.b64encode(await gray.read()).decode('utf-8')
    async with aiof.open(file_uid+'_c'+'.png', 'rb') as color:
        images['original_color'] = base64.b64encode(await color.read()).decode('utf-8')
    async with aiof.open(file_uid+'_input'+'.png', 'rb') as shaped:
        images['image'] = base64.b64encode(await shaped.read()).decode('utf-8')
    for path in cleanup_paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception as ex:
            eprint(str(ex))
            pass
    return images


async def handle_spectrogram_request(req_data, spectro_type):
    global APP_STATE
    try:
        req_json = APP_STATE.serializer.loads(req_data)
    except Exception as ex:
        eprint(str(ex))
        return jsonify({
            'msg': 'payload did not have valid signature',
            'ex': str(ex)
            })
    if 'data' in req_json and 'ext' in req_json:
        data = req_json['data']
        cleanup_paths = []
        try:
            # this will be audio
            raw_data = base64.b64decode(data)
            file_uid = str(uuid.uuid4()).replace('-', '')
            upload_path = file_uid+'.'+req_json['ext']
            async with aiof.open(upload_path, 'wb') as f:
                await f.write(raw_data)
            cleanup_paths.append(upload_path)
            file_location = file_uid+'.'+req_json['ext']
            return_data = await gen_spectrogram(raw_data, file_location, spectro_type)
        except Exception as ex:
            eprint(str(ex))
            return_data = {
                'msg': 'spectrogram generation failed',
                'ex': str(ex)
            }
            pass
        try:
            for path in cleanup_paths:
                if os.path.isfile(path):
                    os.remove(path)
        except Exception as ex:
            eprint(str(ex))
            pass
        return return_data
    return {'msg':'something went wrong'}


@app.route('/melspectrogram', methods=['POST'])
async def get_melspectrogram():
    return jsonify(await handle_spectrogram_request(await request.get_data(), 'melspectrogram'))


@app.route('/chromagram', methods=['POST'])
async def get_chromagram():
    return jsonify(await handle_spectrogram_request(await request.get_data(), 'chromagram'))


@app.route('/dbspectrogram', methods=['POST'])
async def get_dbspectrogram():
    return jsonify(await handle_spectrogram_request(await request.get_data(), 'dbspectrogram'))


@app.route('/restartsignal', methods=['POST'])
async def restart_signal():
    global APP_STATE
    req_data = await request.get_data()
    try:
        req_json = APP_STATE.serializer.loads(req_data)
        if 'restart' in req_json and req_json['restart'] is True and 'ALLOW_RESTART_SIGNAL' in os.environ and os.environ['ALLOW_RESTART_SIGNAL'] == 'true':
            sys.exit(0)
    except Exception as ex:
        eprint(str(ex))


async def handle_work_queue_spectrograms(work):
    global APP_STATE
    if 'work' not in work:
        return (None, dict())
    if 'item' not in work:
        return (None, dict())
    if work['work'] is False:
        return (None, dict())
    if work['item'] is None:
        return (None, dict())
    item = work['item']
    if 'ext' in work:
        ext = work['ext']
    else:
        ext = 'music_file'
    raw_data = base64.b64decode(item['data'])
    del(item['data'])
    del(work['item'])
    uid = str(uuid.uuid4())
    file_location = uid+'.'+ext
    try:
        async with aiof.open(file_location, 'wb') as f:
            await f.write(raw_data)
        if 'spectro_type' not in item:
            return_data = [{spec_type: await gen_spectrogram(raw_data, file_location, spec_type)} for spec_type in ["melspectrogram", "chromagram", "dbspectrogram"]]
        if 'spectro_type' in item:
            return_data = await gen_spectrogram(raw_data, file_location, item['spectro_type'])
    except Exception as ex:
        eprint(str(ex))
        return (False, dict())
        pass
    try:
        if os.path.isfile(file_location):
            os.remove(file_location)
    except Exception as ex:
        eprint(str(ex))
        return (False, dict())
        pass
    return (True, {**item, **work, 'spectrograms': return_data})


async def watcher(event_loop):
    while True:
        try:
            then = datetime.datetime.now()
            if 'ENABLE_PULL_SERVICE' in os.environ and os.environ['ENABLE_PULL_SERVICE'] == 'true':
                await puller()
                while await check_before_exit() is False:
                    await puller()
            if 'NO_PERSISTENCE' in os.environ and os.environ['NO_PERSISTENCE'] == 'true':
                sys.exit(0)
            if (datetime.datetime.now()-then).total_seconds() < 2.0:
                await asyncio.sleep(5)
        except Exception as ex:
            eprint(str(ex))
            await asyncio.sleep(5)
            pass
    await asyncio.sleep(0.1)


async def check_before_exit():
    async with httpx.AsyncClient() as client:
        check = await client.post(get_srv_record_url('GENREML_FRONTEND_PORT', 'GENREML_FRONTEND_ADDRESS', 'GENREML_FRONTEND_SCHEMA', False)+'/spectrogramsafetoreboot', data=APP_STATE.signer.sign(APP_STATE.uid), timeout=60.0)
        check = check.json()
        return check["safe"]


async def puller():
    run_limit = 10
    if 'RUN_LIMIT' in os.environ and (re.match("^[0-9]+$", os.environ['RUN_LIMIT']) is not None):
        run_limit = int(os.environ['RUN_LIMIT'])
    for i in range(run_limit):
        then = datetime.datetime.now()
        while (datetime.datetime.now()-then).total_seconds() < 15:
            async with httpx.AsyncClient() as client:
                try:
                    work = await client.post(get_srv_record_url('GENREML_FRONTEND_PORT', 'GENREML_FRONTEND_ADDRESS', 'GENREML_FRONTEND_SCHEMA', False)+'/spectrograms', data=APP_STATE.signer.sign('spectrogram_request'), timeout=600.0)
                    work.raise_for_status()
                except Exception as ex:
                    eprint("error client call")
                    eprint(str(ex))
                    await asyncio.sleep(0.5)
                    return
                post_data = await handle_work_queue_spectrograms(work.json())
                if post_data[0] is True:
                    post_data = post_data[1]
                    async with httpx.AsyncClient() as client:
                        try:
                            send_back = await client.post(get_srv_record_url('GENREML_FRONTEND_PORT', 'GENREML_FRONTEND_ADDRESS', 'GENREML_FRONTEND_SCHEMA', False)+'/finishedspectrograms', data=APP_STATE.serializer.dumps(post_data), timeout=600.0)
                            send_back.raise_for_status()
                        except Exception as ex:
                            eprint("error in posting spectrogram results")
                            eprint(str(ex))
                            return
            await asyncio.sleep(0.3)


event_loop = None
APP_STATE = None
@app.before_serving
async def start():
    global event_loop
    global APP_STATE
    event_loop = asyncio.get_event_loop()
    APP_STATE = app_state(event_loop)
    if 'ENABLE_PULL_SERVICE' in os.environ and os.environ['ENABLE_PULL_SERVICE'] == 'true':
        event_loop.create_task(watcher(event_loop))
