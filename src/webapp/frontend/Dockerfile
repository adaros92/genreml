FROM python:latest

RUN python3 -m pip install quart aiohttp
RUN mkdir /filestore
ADD static /opt/static/
ADD templates /opt/templates/
COPY app.py /opt/

CMD ["hypercorn", "--certfile", "/certs/server.crt", "--keyfile", "/certs/server.key", "--bind", "0.0.0.0:443", "/opt/app:app"]