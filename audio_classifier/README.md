# ML Audio Classification
```***FMA_model.h5 model needs to be moved audio_classifier directory or path in audi-classifier.py modified to local .h5 file***```

Install dependencies:
```
pip3 install -r requirements.txt
```
# Description
```
python3 audio-classifier.py [OPTIONS] [PATH/URL] [N]
```
# Options
    -l          Classify audio file from local machine 
    -y          Classify audio from youtube url source 
# Inputs 
    [PATH/URL]  Local file PATH or youtube URL
    [N]         Top N predictions (1-32)
# Examples
```
python3 audio-classifier.py -l ./000002.mp3 3
python3 audio-classifier.py -y https://www.youtube.com/watch?v=QKcNyMBw818 5
```
