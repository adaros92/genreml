import logging
from genreml.model.cnn import config

import urllib.request


def download_model():
    """ Download h5 model from public AWS S3 bucket"""
    logging.info("[genreml] Downloading model...")
    with urllib.request.urlopen(config.FMAModelConfig.FMA_MODEL_URL) as f:
        data = f.read()
        open(config.FMAModelConfig.FMA_MODEL_PATH, 'wb').write(data)
    logging.info("[genreml] Model download complete")
