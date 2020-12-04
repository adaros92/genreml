FROM tensorflow/tensorflow:latest

RUN apt-get update && apt-get install -y curl gnupg git build-essential ffmpeg libsndfile1-dev libasound2-dev
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install dnspython httpx itsdangerous numpy quart requests keras pandas autokeras scipy aiofiles Pillow matplotlib simpleaudio librosa youtube-dl eyed3
#RUN python3 -m pip install git+https://github.com/adaros92/CS467-Project.git@feature/additional_librosa_features
# Main
# RUN python3 -m pip install git+https://github.com/adaros92/CS467-Project.git
# Official
RUN python3 -m pip install genreml
RUN curl https://raw.githubusercontent.com/adaros92/CS467-Project/main/webapp/frontend/processing/downloader.py > /opt/downloader.py
RUN mkdir /opt/spectrogram_store
RUN mkdir /opt/prediction_store
RUN mkdir /opt/clip_store
RUN mkdir /opt/file_store
ADD static /opt/static/
ADD templates /opt/templates/
COPY *.csv /opt/
COPY *.pkl /opt/
COPY *.mp3 /opt/
COPY *.csv /
COPY *.pkl /
COPY *.mp3 /
COPY audio_classifier.py /opt/audio_classifier.py
COPY app.py /opt/app.py

CMD ["hypercorn", "--bind", "0.0.0.0:80", "/opt/app:app"]