FROM python:latest

RUN apt-get update
RUN apt install -y ffmpeg
RUN python3 -m pip install SoundFile librosa quart aiohttp itsdangerous numpy

COPY app.py /opt/app.py

CMD ["python3"]