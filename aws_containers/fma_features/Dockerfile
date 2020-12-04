FROM tensorflow/tensorflow:latest

RUN python3 -m pip install --upgrade pip
RUN apt-get update
RUN apt-get install -y curl gnupg git build-essential ffmpeg libasound2-dev libsndfile1-dev
RUN python3 -m pip install 'scikit-learn==0.22.2.post1'
# removed packages
# scikit-learn
# numpy
RUN python3 -m pip install aiofiles dnspython httpx itsdangerous librosa matplotlib pandas Pillow quart requests scipy SoundFile
RUN python3 -m pip install simpleaudio librosa youtube-dl eyed3
# Dev branch test
RUN python3 -m pip install git+https://github.com/adaros92/CS467-Project.git@feature/additional_librosa_features
# Main
# RUN python3 -m pip install git+https://github.com/adaros92/CS467-Project.git
# Official
# RUN python3 -m pip install genreml
COPY *.csv /opt/
COPY *.pkl /opt/
COPY *.csv /
COPY *.pkl /
COPY *.mp3 /
COPY *.py /opt/
COPY app.py /opt/app.py
# deprecated after pypi distribution
#ADD genreml /opt/genreml

CMD ["hypercorn", "--bind", "0.0.0.0:443", "/opt/app:app"]