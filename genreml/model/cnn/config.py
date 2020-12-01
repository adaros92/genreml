from genreml.model.utils import file_handling
import pkg_resources


class CnnModelConfig:
    IMG_PIXELS = 67000
    IMG_WIDTH = 335
    IMG_HEIGHT = 200


class FMAModelConfig:
    FMA_MODEL_PATH = pkg_resources.resource_filename('genreml', 'model/cnn/data/FMA_model.h5')
    FMA_MODEL_URL = 'https://fma-trained-model.s3.us-east-2.amazonaws.com/FMA_model.h5'
