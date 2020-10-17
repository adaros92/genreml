from quart import Quart, request, jsonify, abort, redirect, url_for
import aiohttp
import asyncio
import base64
from functools import reduce
import json
import os
import re
import uuid
import model as keras_model
import request_to_train


app = Quart(__name__)


class app_state:
    def __init__(self, loop):
        self.loop = loop
        self.token_registry = set()
    # does not need to be async now
    # but tokens could come from API
    # in future
    async def get_model_request_token(self):
        token = str(uuid.uuid4()).replace('-', '')
        while token in self.token_registry:
            token = str(uuid.uuid4()).replace('-', '')
        self.token_registry.add(token)
        return token


def validate_positive_int(value):
    if type(value) == str and re.match('^[0-9]+$', value) is not None:
        value = int(value)
    if type(value) != int:
        return None
    if value < 1:
        return None
    return value


def validate_positive_float(value):
    if type(value) == str and re.match('^[0-9]+\.[0-9]+$', value) is not None:
        value = float(value)
    if type(value) != float:
        return None
    if value < 0.0:
        return None
    return value


def validate_dataset(dataset):
    if type(dataset) != list:
        return None
    if reduce(lambda a,b: a is True and b is True, map(lambda x: type(x) is dict, dataset)) is False:
        return None
    return dataset


@app.route('/buildmodel',methods=['POST'])
async def build_model():
    global APP_STATE
    data = await request.get_json()
    layers=None
    epochs=None
    batch_size=None
    if 'layers' in data:
        layers = validate_positive_int(data['layers'])
    if layers is None:
        return jsonify({
            'error': True,
            'msg': 'layers must be integer'
        })
    if 'epochs' in data:
        epochs = validate_positive_int(data['epochs'])
    if epochs is None:
        return jsonify({
            'error': True,
            'msg': 'epochs must be integer'
        })
    if 'batch_size' in data:
        batch_size = validate_positive_int(data['batch_size'])
    if batch_size is None:
        return jsonify({
            'error': True,
            'msg': 'batch_size must be integer'
        })
    if 'test_size' in data:
        test_size = validate_positive_float(data['test_size'])
    if test_size is None:
        return jsonify({
            'error': True,
            'msg': 'test_size must be a float'
        })
    if 'dataset' in data:
        dataset = validate_dataset(data['dataset'])
    if dataset is None:
        return jsonify({
            'error': True,
            'msg': 'dataset must be a list of dictionaries'
        })
    token = await APP_STATE.get_model_request_token()
    # block of code should be moved and refactored
    training_data = await request_to_train.build_dataset(dataset, test_size)
    if training_data[0] is True:
        training_data = training_data[1]
        build_req = await keras_model.build_model(layers, epochs, batch_size, training_data['X_train'], training_data['y_train'], training_data['X_test'], training_data['y_test'])
        if build_req[0] is True:
            model = build_req[1][0]
            model.save('/opt/model_store/'+token+'.h5')
            return jsonify({
                'token': token,
                'msg': 'model saved!'
            })
        else:
            ret = {
                'msg': 'request to build model failed'
            }
            if build_req[0] is False:
                ret['ex'] = str(build_req[1][0])
            return jsonify(ret)
    else:
        return jsonify({"message": "failed to build training dataset"})
    # end block
    return jsonify({"message": "build may have failed"})


@app.route('/getmodel',methods=['POST'])
async def get_model():
    global APP_STATE
    data = await request.get_json()
    if 'token' in data:
        token = data['token']
        if re.match(r'^[a-fA-F0-9]{32}$', token) is not None:
            if os.path.isfile('/opt/model_store/'+token+'.h5'):
                with open('/opt/model_store/'+token+'.h5', 'rb') as m:
                    mr = base64.b64encode(m.read()).decode('utf-8')
                return jsonify({
                    'model': mr,
                    'ext': 'h5',
                    'name': token,
                    'state': 'complete'
                })
            if token in APP_STATE.token_registry:
                return jsonify({
                    'state': 'pending',
                    'msg': 'token found, no available model'
                })
            return jsonify({
                'msg': 'model not found',
                'error': 'token invalid'
            })
        return jsonify({
            'msg': 'valid token required'
        })
    return jsonify({
        'state': 'unknown'
    })


# this deals with problem that sometimes
# async scheduler may not be "awake" and
# may not schedule some pending tasks.
# also we can put different state checks
# here and take action if state is bad
# or some type of internal state update
# must be performed
async def watcher():
    await asyncio.sleep(5)


event_loop = None
APP_STATE = None
@app.before_serving
async def start():
    global event_loop
    global APP_STATE
    event_loop = asyncio.get_event_loop()
    APP_STATE = app_state(event_loop)
    keras_model.event_loop = event_loop
    request_to_train.event_loop = event_loop
    event_loop.create_task(watcher())
