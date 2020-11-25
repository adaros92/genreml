FROM tensorflow/tensorflow:latest

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install dnspython httpx itsdangerous numpy quart requests
RUN mkdir /filestore
ADD static /opt/static/
ADD templates /opt/templates/
COPY app.py /opt/app.py

CMD ["hypercorn", "--bind", "0.0.0.0:80", "/opt/app:app"]