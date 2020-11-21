# CS467-Project
Repo for the CS467 capstone project

### Contributing

##### Git
The usual flow will be as follows.

1. Clone the repo
```
git clone git@github.com:adaros92/CS467-Project.git
```
2. Create new feature branch as feature/[name]
```
git checkout main
git pull
git checkout -b feature/initial-structure
```
3. Add code/make changes in feature branch
4. Commit to remote
```
git add .
git commit -m "Add initial structure to repository and contributing section to readme.md"
git push origin feature/initial-structure
```
5. Submit a pull request at https://github.com/adaros92/CS467-Project/pulls from your feature branch to the main branch
6. Resolve any comments locally and push a new revision to be reviewed
7. Solve any merge conflicts and merge the pull request

Useful git commands and references.

* Display available branches `git branch`
* Squashing commits into one for cleanliness https://gist.github.com/patik/b8a9dc5cd356f9f6f980
* Merge branch 
```
git checkout main
git merge other-branch
```
* Gitflow documentation https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow

##### Python Environment and Style
It's recommended to use the Pycharm IDE for making contributions. You can get it for free here: https://www.jetbrains.com/pycharm/. This will help you catch style and syntax issues early. 

We will try to follow PEP 8 whenever possible as documented here: https://www.python.org/dev/peps/pep-0008/. If you use Pycharm then you won't need to read this because it will highlight issues for you :). 

### Installing Genreml
Install dependencies
Mac:
```
brew install ffmpeg
```

Ubuntu/Debian:
```
sudo apt-get install ffmpeg
```

To install the package from Pypi as documented in https://pypi.org/project/genreml run:
```
pip3 install genreml
or
pip install genreml
```

To install the package from the repo with Unix-based OS run the following in CS467-Project directory
```
bash install.sh
```

Test the installation by running the following in your terminal:
```
genreml
```

If the installation fails, ensure you have pip installed and that pip is correctly mapped (it may be pip3 on your system). If the genreml command
doesn't work then run the following as the entry point to the CLI.
```
python3 -m model
```

Alternatively, you can travel to the src/model and run the following as the main entry point without installing the app
```
python3 __main__.py
```

# Running the CLI

**The youtube functionality is not currently working due to youtube-dl takedown**

Downloading audio files to your machine (**This is no longer working due to youtube-dl takedown**)
```
genreml download -s "Black Dog" -a "Led Zeppelin"
```

You can do the same without installing the app by traveling to the model package and running
```
python3 __main__.py download -s "Black Dog" -a "Led Zeppelin"
```

Processing audio files stored in some drive on your machine
```
genreml process -fp "/Users/adamsrosales/Documents/audio-clips/"
```

You can do the same without installing the app by traveling to the model package and running
```
python3 __main__.py process -fp "/Users/adamsrosales/Documents/audio-clips/"
```

The same can be run with a single file
```
genreml process -fp "/Users/adamsrosales/Documents/audio-clips/Yummy_Justin Bieber_clip.wav"
```

To ignore certain features from the feature extraction process
```
# Ignore spectrogram generation
genreml process -fp "/Users/adamsrosales/Documents/audio-clips/fma_small/000" -e spectrogram
```

To change audio file type
```
genreml process -fp "/Users/adamsrosales/Documents/audio-clips/fma_small/000" -af mp3
```

To change export color images and change image size to X in wide by Y in high
```
genreml process -fp "/Users/adamsrosales/Documents/audio-clips/fma_small/000" -cmap None -fw 15.0 -fh 5.0
```

# Using genreml as a Package in Python

You can import genreml after a successful installation like any Python package
```
import genreml
```

See genreml/model/__main__ for the hooks into the genreml functionality that the CLI has. Some examples below.

Run feature extraction on sample FMA MP3s packaged with application.
```
from genreml.model.processing import audio

audio_files = audio.AudioFiles()
audio_files.extract_sample_fma_features()
```

audio.AudioFiles() just creates a dictionary of individual file paths to audio data. You can extract the data from the
collection as you would with any dictionary.
```
audio_signals = []
sample_rates = []
for audio_key, object in audio_files.items():
    audio_signals.append(object.audio_rate)
    sample_rates.append(object.sample_rates)
```

You can also get all of the visual and non-visual features extracted from the audio collection itself.
```
my_features = audio_files.features
my_visual_features = audio_files.visual_features
```

Convert features to Pandas data frame
```
df = audio_files.to_df()
```

Run feature extraction on a directory or filepath of your choice
```
audio_files.extract_features("[YOUR_FILE_PATH]")
```

Run feature extraction on a directory or filepath of your choice but export results to a destination filepath
```
audio_files.extract_features("[YOUR_FILE_PATH]", destination_filepath="[YOUR_DESTINATION_PATH]")
```

Change color of images generated from feature extraction
```
audio_files.extract_features("[YOUR_FILE_PATH]", destination_filepath="[YOUR_DESTINATION_PATH]", cmap=None)
```

Change size of images generated to 15 by 5 inches
```
audio_files.extract_features(
    "[YOUR_FILE_PATH]", destination_filepath="[YOUR_DESTINATION_PATH]",
    figure_width=15, figure_height=5
)
```