FROM python:3.8

RUN apt-get update 
RUN apt-get install -y curl gnupg 
RUN curl https://pkgs.tailscale.com/stable/debian/buster.gpg | apt-key add -
RUN curl https://pkgs.tailscale.com/stable/debian/buster.list | tee /etc/apt/sources.list.d/tailscale.list
RUN apt-get update 
RUN apt-get install -y tailscale
RUN python3 -m pip install tensorflow keras pandas numpy scikit-learn quart aiohttp
COPY startup.sh /startup.sh
COPY app.py /opt/app.py
COPY model.py /opt/model.py
COPY request_to_train.py /opt/request_to_train.py
RUN mkdir /opt/model_store
ENV TAILSCALE_PORT="80"

CMD ["/startup.sh"]