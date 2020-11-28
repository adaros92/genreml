# Name: config.py
# Description: defines configurations for the various components of audio extraction and processing


class AudioConfig:
    # The format to store audio in
    AUDIO_FORMAT = 'mp3'
    # Prefix to save audio features to
    FEATURE_DESTINATION = '/features/'
    # Checkpoint frequency in number of tracks processed
    CHECKPOINT_FREQUENCY = 10
    # Minimum required clip length for prediction
    MIN_CLIP_LENGTH = 29


class DisplayConfig:
    # What cmap to use when saving visual features
    # Refer to https://matplotlib.org/3.3.2/api/_as_gen/matplotlib.axes.Axes.imshow.html
    CMAP = "Greys"
    # Defines the size of the figures created by display
    FIGSIZE_WIDTH = 10
    FIGSIZE_HEIGHT = 10


class FeatureExtractorConfig:
    # The Librosa features supported by the CLI
    SUPPORTED_FEATURES = ['chroma_stft', 'rms', 'spec_cent', 'spec_bw', 'spec_rolloff', 'zcr', 'mfcc']
    NUMBER_OF_MFCC_COLS = 20
    # How to aggregate the features
    FEATURE_AGGREGATION = ['mean', 'min', 'max', 'std']
    N_FFT = 2048
    HOP_LENGTH = 1024
