# CS467-Project Web Frontend Container

To build the docker container:

```
docker build -t music:frontend .
```

To run the docker container

```
docker run -v /certs:/certs -p 443:443 -dit music:frontend
```

This binds to server port 443 and the volume mount provides server certs. App expects a server.key and and server.crt to run. These defaults can be changed by changing the default run command in the Dockerfile.
