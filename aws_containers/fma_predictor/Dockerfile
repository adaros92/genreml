FROM tensorflow/tensorflow:latest

RUN apt-get update
RUN apt-get install -y curl gnupg nodejs npm git build-essential ffmpeg libasound2-dev libsndfile1-dev
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
# node installs
RUN useradd -ms /bin/bash node
RUN chown -R node:node /home/node
USER node
ENV HOME /home/node
WORKDIR /home/node/
RUN npm install express morgan body-parser multer
USER root
WORKDIR /
RUN mv /home/node/node_modules /opt/node_modules
RUN userdel node
RUN chown -R root:root /opt/node_modules
# normal configs
RUN mkdir /opt/model_store
RUN mkdir /opt/temp_model_uploads
COPY startup.sh /startup.sh
COPY *.csv /opt/
COPY *.pkl /opt/
COPY *.csv /
COPY *.pkl /
COPY *.mp3 /
COPY *.py /opt/
COPY uploads.js /opt/upload.js
# deprecated after pypi distribution
# ADD genreml /opt/genreml
# This should be done another way
# temp for testing
COPY 68b1d64e0635f36d1a71d1b2c7000a69b6d02dcccfaa9893408f93fe603faf39.h5 /opt/model_store/68b1d64e0635f36d1a71d1b2c7000a69b6d02dcccfaa9893408f93fe603faf39.h5
COPY app.py /opt/app.py

CMD ["/startup.sh"]