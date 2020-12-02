from genreml.model.processing.config import AudioConfig
import pkg_resources


class CnnModelConfig:
    IMG_PIXELS = 67000
    IMG_WIDTH = 335
    IMG_HEIGHT = 200


class FMAModelConfig:
    FMA_MODEL_PATH = pkg_resources.resource_filename('genreml', 'model/cnn/data/FMA_model.h5')
    FEATURES_PATH = pkg_resources.resource_filename('genreml', 'model/cnn/data/features')
    FMA_MODEL_URL = 'https://fma-trained-model.s3.us-east-2.amazonaws.com/FMA_model.h5'
    SPECT_IMG_PATH = pkg_resources.resource_filename('genreml', 'model/cnn/data')
    TMP_SONG_PATH = pkg_resources.resource_filename('genreml', 'model/cnn/data/temp_song')
    LABELS_PATH = pkg_resources.resource_filename('genreml', 'model/cnn/data/labels_key.csv')
    FEATURE_COLS = pkg_resources.resource_filename('genreml', 'model/cnn/data/feature_cols.csv')
    PKL_PATH = pkg_resources.resource_filename('genreml', 'model/cnn/data/std_scaler_B.pkl')

