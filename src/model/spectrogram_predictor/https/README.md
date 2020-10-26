# CS467-Project Web Frontend Container

To build the docker container the build.sh script can be used. Currently it just does the command below, but may be customized further in the future.

```
docker build -t spectrogrampredictor .
```

On a server instance deployment can be done by running the container with the command below. When deployed where the API is publicly exposed, currently signing token are used and are stored as an environment variable set at runtime.

```
docker run --restart always --name spectrogrampredictor --hostname=spectrogrampredictor -v /certs:/certs -p 443:443 -p 4443:4443 -e SIGNING_TOKEN=$SIGNING_TOKEN -dit $CONTAINER_IMAGE
```

This binds to server port 443 and 4443 and the volume mount provides server certs. App expects a server.key and and server.crt to run. This command will make the /certs directory on the host available inside of the container at /certs.


# Uploading a model, a song, and getting a prediction

Note: the examples below build on each other, so some of the snippets of code from above may be required to run examples at the bottom.


First read and store the model:

```python
import base64

with open('GTZAN_model.h5', 'rb') as mf:
    model = mf.read()
    model_b64 = base64.b64encode(model)
```

Test the python endpoint

```python
import httpx

predict_url = 'https://ironnoesis.net:443'
httpx.get(predict_url+'/test').content
```

There is also a NodeJS endpoint because sometimes while uploading large files, the python endpoint was dropping connections.

Test the NodeJS endpoint:

```python
predict_node_url = 'https://ironnoesis.net:4443'
httpx.get(predict_node_url+'/test').content
```

To prevent anyone from utilizing these endpoints, posted requests are checked for a valid signature.

```python
import itsdangerous

signer = itsdangerous.Signer('<INSERT_SIGNING_TOKEN>')
serial = itsdangerous.Serializer('<INSERT_SIGNING_TOKEN>')
```

Before uploading the model, register it's hash with the endpoint. Any model uploaded to the NodeJS endpoint without being registered first will be deleted. If registered and matching a stored hash, the model will be moved to the model storage directory.

```python
hash_register = httpx.post(predict_url+'/registermodelhash', data=serial.dumps({
    'hash':hashlib.sha256(model).hexdigest()
}))
hash_register.content

>>> b'{"msg":"model hash stored"}'
```

Now upload the model

```python
files = [
    ('model', ('model', model, 'application/octet'))
]
model_upload = httpx.post(predict_node_url+'/nodemodeluploads', files=files, timeout=30)

model_upload.content
>>> b'{"message":"file uploaded!","uploaded":true}'
```

This call will ensure that any models in the temp directory from NodeJS are hashed and moved if they've been registered. Because this also happens periodically as background scheduled task, one may not get the model back in the response.

```python
httpx.get(predict_url+'/hashmodels')
```

The call below should work for the python endpoint. In testing, uploads to NodeJS were more reliable.

```python
files = [
    ('model', ('model', signer.sign(model), 'application/octet'))
]
model_upload = httpx.post(predict_url+'/nodemodeluploads', files=files, timeout=30)
```

# Example of uploading a song and getting a prediction

To avoid creating a csv file for a single row of data, the example below uses buffers. A csv is uploaded, base64 encoded, and used for single rows so that on the other end all of the columns are in the same order which could affect model accuracy. Dictionaries do not keep their keys in a deterministic order. Required fields are the hash of the model file you would like to use for prediction, the file extension, the music file (base64 encoded), and the row of data in csv format (base64 encoded). The current model assumes the same input as the notebook in colab (Music Genre Classification_v2.ipynb) which are (?, 235, 335, 1) for the spectrogram and (?, 58) for features.

```python
import pandas as pd
import io

features = pd.read_csv('features_30_sec.csv')
csv_buf = io.StringIO()
features[features['filename'] == 'rock.00092.wav'].drop(['filename','label'],axis=1).to_csv(csv_buf)
csv_b_buf = io.BytesIO(csv_buf.read().encode('utf-8'))
csv_b_buf.seek(0)

song_upload = {
    'model_hash': registered_model_hash,
    'ext': 'wav',
    'data': music_b64.decode('utf-8'),
    'csv':base64.b64encode(csv_b_buf.read()).decode('utf-8')
}
song_prediction = requests.post(predict_url+'/prediction', data=serial.dumps(song_upload))

song_prediction.content
>>> b'{"array":[[0.0,1.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]]}'
```
