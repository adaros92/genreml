FROM python:latest

RUN python3 -m pip install quart aiohttp
RUN mkdir /filestore
ADD public /opt/static/
COPY app.py /opt/

CMD ["hypercorn", "--certfile", "/certs/server.crt", "--keyfile", "/certs/server.key", "--bind", "0.0.0.0:443", "/opt/app:app"]