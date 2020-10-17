# CS467-Project Web Frontend Container

To build the docker container:

```shell
docker build -t music:frontend .
```

The docker build command automates building the app and preparing it for deployment.

On a server instance deployment can be done by running the container with the command:

```shell
docker run -v /certs:/certs -p 443:443 -dit music:frontend
```

# Generating SSL Certs for local HTTPS Testing

This binds to server port 443 and the volume mount provides server certs. App expects a server.key and and server.crt to run. This command will make the /certs directory on the host available inside of the container at /certs. These defaults can be changed by changing the default run command in the Dockerfile.

```shell
openssl genrsa -aes256 -out ca.key 4096

openssl req -x509 -new -nodes -key ca.key -sha256 -days 1095 -out ca.pem

openssl x509 -in ca.pem -inform PEM -out ca.crt

openssl genrsa -out server.key 4096

openssl req -new -key server.key -out server.csr
```

Then edit a the conf file

```
vim server.ssl.conf
```

Place into file:


subjectAltName = @alt_names

[alt_names]
DNS.1   = arch.local
DNS.2   = server.arch.local


Then do 

```shell
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial -CAserial ca.seq -out server.crt -days 1095 -sha256 -extfile server.ssl.conf
```

Then server.crt and ca.crt need to be added to the machines trust store. The process varies based on OS.

I would recommend only placing server.crt and server.key in the certs deployment directory and when necessary server.key, server.crt, and ca.crt. The other files are not needed and can be a risk if leaked.
