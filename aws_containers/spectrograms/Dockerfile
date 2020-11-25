FROM tensorflow/tensorflow:latest

RUN python3 -m pip install --upgrade pip
RUN apt-get update
RUN apt-get install -y curl gnupg git build-essential ffmpeg libasound2-dev libsndfile1-dev
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install itsdangerous pandas numpy quart httpx
RUN python3 -m pip install requests aiofiles SoundFile librosa Pillow matplotlib
# Dev branch test
RUN python3 -m pip install git+https://github.com/adaros92/CS467-Project.git@feature/additional_librosa_features
# Main
# RUN python3 -m pip install git+https://github.com/adaros92/CS467-Project.git
# Official
# RUN python3 -m pip install genreml
COPY app.py /opt/app.py
# deprecated after pypi distribution
#ADD genreml /opt/genreml

CMD ["hypercorn", "--bind", "0.0.0.0:80", "/opt/app:app"]