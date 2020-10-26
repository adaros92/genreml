FROM python:3.8

RUN apt-get update 
# RUN apt-get install -y curl gnupg 
RUN apt-get install -y curl gnupg ffmpeg nodejs npm
RUN curl https://pkgs.tailscale.com/stable/debian/buster.gpg | apt-key add -
RUN curl https://pkgs.tailscale.com/stable/debian/buster.list | tee /etc/apt/sources.list.d/tailscale.list
RUN apt-get update 
RUN apt-get install -y tailscale
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install tensorflow keras pandas numpy scikit-learn quart aiohttp httpx git+https://github.com/keras-team/keras-tuner.git@1.0.2rc3 autokeras
RUN python3 -m pip install requests aiofiles SoundFile librosa Pillow matplotlib
##
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
##
RUN mkdir /opt/model_store
RUN mkdir /opt/temp_model_uploads
COPY startup.sh /startup.sh
COPY app.py /opt/app.py
COPY uploads.js /opt/upload.js
ADD model /opt/model

ENV TAILSCALE_PORT="80"

CMD ["/startup.sh"]