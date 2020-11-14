# Name: config.py
# Description: defines configurations for the various components of audio extraction and processing


class AudioConfig:
    # The format to store audio in
    AUDIO_FORMAT = 'mp3'
    # Prefix to save audio features to
    FEATURE_DESTINATION = '/features/'
    # Checkpoint frequency in number of tracks processed
    CHECKPOINT_FREQUENCY = 10


class DisplayConfig:
    # What cmap to use when saving visual features
    # Refer to https://matplotlib.org/3.3.2/api/_as_gen/matplotlib.axes.Axes.imshow.html
    CMAP = "Greys"
    # Defines the size of the figures created by display
    FIGSIZE_WIDTH = 10
    FIGSIZE_HEIGHT = 10


class YoutubeExtractionConfig:
    # URL to make request to for audio results
    SEARCH_URL = 'https://www.youtube.com/results'
    # Query parameters to filter requests to search URL by
    SEARCH_QUERY_PARAMS = ['search_query']
    # URL to make request to for actual audio data
    CONTENT_URL = 'https://www.youtube.com/watch'
    # Query parameters to filter requests to content URL by
    CONTENT_QUERY_PARAMS = ['v']
    # Post-processor key to use
    POST_PROCESSOR_KEY = 'FFmpegExtractAudio'
    # Post-processor audio quality
    POST_PROCESSOR_QUALITY = '192'
    # Preferred audio quality name
    PREFERRED_AUDIO_QUALITY = 'bestaudio/best'


class SongExtractorConfig:
    # A list of supported sources by the package
    SUPPORTED_SOURCES = ['youtube']
    # Where to save audio files to
    DESTINATION_FILEPATH = '/Documents/audio-clips/'


class FeatureExtractorConfig:
    # The Librosa features supported by the CLI
    SUPPORTED_FEATURES = ['chroma_stft', 'rms', 'spec_cent', 'spec_bw', 'spec_rolloff', 'zcr', 'mfcc']
    NUMBER_OF_MFCC_COLS = 20
    # How to aggregate the features
    FEATURE_AGGREGATION = ['mean', 'min', 'max', 'std']
    N_FFT = 2048
    HOP_LENGTH = 1024
