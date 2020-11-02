# CS467-Project Web Frontend Container

To build the docker container:

```
docker build -t music:frontend .
```

The docker build command automates building the app and preparing it for deployment.

On a server instance deployment can be done by running the container with the command:

```
docker run -v /certs:/certs -p 443:443 -dit music:frontend
```

This binds to server port 443 and the volume mount provides server certs. App expects a server.key and and server.crt to run. This command will make the /certs directory on the host available inside of the container at /certs. These defaults can be changed by changing the default run command in the Dockerfile.
