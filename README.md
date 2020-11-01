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

### Running Audio Extraction and Processing Locally
Install dependencies
Mac:
```
brew install ffmpeg
```

Ubuntu/Debian:
```
sudo apt-get install ffmpeg
```

To install the package with Unix-based OS run the following in CS467-Project directory
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

### Web-app Development
TBU

To deploy app to production.

TBU

### Model Development
TBU
