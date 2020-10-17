FROM python:3.8

RUN apt-get update 
RUN apt-get install -y curl gnupg 
RUN curl https://pkgs.tailscale.com/stable/debian/buster.gpg | apt-key add -
RUN curl https://pkgs.tailscale.com/stable/debian/buster.list | tee /etc/apt/sources.list.d/tailscale.list
RUN apt-get update 
RUN apt-get install -y tailscale
RUN python3 -m pip install quart requests httpx aiofiles
COPY startup.sh /startup.sh
COPY app.py /opt/app.py
RUN mkdir /opt/datastore/
ENV TAILSCALE_PORT="80"

CMD ["/startup.sh"]