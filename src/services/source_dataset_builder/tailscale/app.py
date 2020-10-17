from quart import Quart, request, jsonify, abort, redirect, url_for
import asyncio
import aiofiles as aiof
import base64
import httpx
import json
import os
import re
import requests
import tarfile
import uuid


app = Quart(__name__)


class app_state:
    def __init__(self, loop):
        self.loop = loop
        self.token_registry = set()
        self.task_registry = dict()
        self.completed_dataset_requests = set()
        self.datastore_root = "/opt/datastore"
    # does not need to be async now
    # but tokens could come from API
    # in future
    async def get_dataset_request_token(self):
        token = str(uuid.uuid4()).replace('-', '')
        while token in self.token_registry:
            token = str(uuid.uuid4()).replace('-', '')
        self.token_registry.add(token)
        return token
    async def set_download_task(self, token, task):
        if token not in self.token_registry:
            return False
        self.task_registry[token] = {
            "task": task,
            "complete": None,
            "results": None,
            "lock": asyncio.Lock()
        }
        self.loop.create_task(wait_for_task(token))
        await asyncio.sleep(0)
        return True


async def wait_for_task(token):
    if token not in APP_STATE.task_registry:
        return
    async with APP_STATE.task_registry[token]["lock"]:
        APP_STATE.task_registry[token]["complete"] = False
    APP_STATE.task_registry[token]["results"] = await APP_STATE.task_registry[token]["task"]
    async with APP_STATE.task_registry[token]["lock"]:
        APP_STATE.task_registry[token]["complete"] = True


async def async_download(url, token):
    global APP_STATE
    try:
        if not os.path.isdir("/".join([APP_STATE.datastore_root, token])):
            os.mkdir("/".join([APP_STATE.datastore_root, token]))
        else:
            return (None, None)
        async with httpx.AsyncClient() as client:
            async with client.stream('GET', url) as response:
                # with open("/".join([APP_STATE.datastore_root, token, token])+".tar.gz", 'wb') as f:
                async with aiof.open("/".join([APP_STATE.datastore_root, token, token])+".tar.gz", 'wb') as f:
                    async for data in response.aiter_bytes():
                        # f.write(data)
                        await f.write(data)
        return (True, "/".join([APP_STATE.datastore_root, token, token])+".tar.gz")
    except Exception as ex:
        return (False, ex)


async def download_and_extract(url, token):
    global APP_STATE
    download = await async_download(url, token)
    if download[0] is True:
        archive = tarfile.open(download[1])
        arch_dir = "/".join(download[1].split("/")[:-1])
        archive.extractall(path=arch_dir)
        archive.close()
        return (True, {
            "token": token,
            "labels": [x for x in os.listdir(arch_dir) if os.path.isdir('/'.join([arch_dir, x]))],
            "status": "done"
        })
    if download[0] is False:
        return (False, {
            "msg": "download attempt failed",
            "error": str(download[1])
        })
    return (None, None)


# this method expects to download a tar.gz file
# it expects the structure to contains at the 
# root folders that are labels for the raw data
# and within each label folder there are files
@app.route('/startdownload',methods=['POST'])
async def start_download():
    global APP_STATE
    data = await request.get_json()
    token = await APP_STATE.get_dataset_request_token()
    if "url" in data:
        url = data["url"] 
        await APP_STATE.set_download_task(token, APP_STATE.loop.create_task(download_and_extract(url, token)))
        await asyncio.sleep(0)
        return jsonify({
            'token': token
        })
    return jsonify({
        "message": "uh oh something went wrong"
    })


@app.route('/checkdownload',methods=['POST'])
async def check_download():
    global APP_STATE
    data = await request.get_json()
    if 'token' in data:
        token = data["token"]
        if re.match(r'^[a-fA-F0-9]{32}$', token) is not None and token in APP_STATE.token_registry:
            if token in APP_STATE.task_registry:
                status = None
                async with APP_STATE.task_registry[token]["lock"]:
                    status = APP_STATE.task_registry[token]["complete"]
                if status is False:
                    return jsonify({
                        "state": "pending"
                    })
                if status is True:
                    return jsonify({
                        "state": "complete",
                        "return": APP_STATE.task_registry[token]["results"][0],
                        "results": APP_STATE.task_registry[token]["results"][1]
                    })
                return jsonify({
                    "state": "starting"
                })
    return jsonify({
        "message": "uh oh something went wrong"
    })


@app.route('/tokenlabels',methods=['POST'])
async def token_labels():
    global APP_STATE
    data = await request.get_json()
    if 'token' in data:
        token = data["token"]
        if re.match(r'^[a-fA-F0-9]{32}$', token) is not None and token in APP_STATE.token_registry:
            if os.path.isdir("/".join([APP_STATE.datastore_root, token])):
                arch_dir = "/".join([APP_STATE.datastore_root, token])
                labels = [x for x in os.listdir(arch_dir) if os.path.isdir('/'.join([arch_dir, x]))]
                return jsonify({
                    "labels": labels
                })
    return jsonify({
        "message": "uh oh something went wrong"
    })


@app.route('/getfilesforlabel',methods=['POST'])
async def get_files_for_label():
    global APP_STATE
    data = await request.get_json()
    if 'token' in data and "label" in data:
        token = data['token']
        label = data["label"]
        if re.match(r'^[a-fA-F0-9]{32}$', token) is not None and token in APP_STATE.token_registry:
            if os.path.isdir("/".join([APP_STATE.datastore_root, token])):
                arch_dir = "/".join([APP_STATE.datastore_root, token])
                labels = set([x for x in os.listdir(arch_dir) if os.path.isdir('/'.join([arch_dir, x]))])
                if label in labels:
                    return jsonify({
                        "files": os.listdir("/".join([APP_STATE.datastore_root, token, label]))
                    })
    return jsonify({
        "message": "uh oh something went wrong"
    })


@app.route('/getfile',methods=['POST'])
async def get_file():
    global APP_STATE
    data = await request.get_json()
    if 'token' in data and "label" in data and "file" in data:
        token = data['token']
        label = data["label"]
        filename = data["file"]
        if re.match(r'^[a-fA-F0-9]{32}$', token) is not None and token in APP_STATE.token_registry:
            if os.path.isdir("/".join([APP_STATE.datastore_root, token])):
                arch_dir = "/".join([APP_STATE.datastore_root, token])
                labels = set([x for x in os.listdir(arch_dir) if os.path.isdir('/'.join([arch_dir, x]))])
                if label in labels:
                    files = set(os.listdir("/".join([APP_STATE.datastore_root, token, label])))
                    if filename in files:
                        with open("/".join([APP_STATE.datastore_root, token, label, filename]), "rb") as f:
                            return f.read()
    return jsonify({
        "message": "uh oh something went wrong"
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
    event_loop.create_task(watcher())
    await asyncio.sleep(0)
