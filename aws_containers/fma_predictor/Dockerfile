FROM tensorflow/tensorflow:latest

RUN apt-get update && apt-get install -y curl gnupg git build-essential ffmpeg libasound2-dev libsndfile1-dev
RUN python3 -m pip install --upgrade pip
# removed packages
# scikit-learn
# numpy
RUN python3 -m pip install 'scikit-learn==0.22.2.post1'
RUN python3 -m pip install itsdangerous keras pandas quart httpx autokeras scipy
RUN python3 -m pip install requests aiofiles Pillow matplotlib dnspython
RUN python3 -m pip install simpleaudio librosa youtube-dl eyed3
# Dev branch test
#RUN python3 -m pip install git+https://github.com/adaros92/CS467-Project.git@feature/additional_librosa_features
# Main
# RUN python3 -m pip install git+https://github.com/adaros92/CS467-Project.git
# Official
# RUN python3 -m pip install genreml
# normal configs
RUN mkdir /opt/model_store
COPY startup.sh /startup.sh
COPY *.csv /opt/
COPY *.pkl /opt/
COPY *.csv /
COPY *.pkl /
COPY *.mp3 /
# deprecated after pypi distribution
# ADD genreml /opt/genreml
# This should be done another way
# temp for testing
COPY 68b1d64e0635f36d1a71d1b2c7000a69b6d02dcccfaa9893408f93fe603faf39.h5 /opt/model_store/68b1d64e0635f36d1a71d1b2c7000a69b6d02dcccfaa9893408f93fe603faf39.h5
COPY audio_classifier.py /opt/audio_classifier.py
COPY app.py /opt/app.py

CMD ["/startup.sh"]