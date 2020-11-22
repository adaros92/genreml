import pandas as pd
import os
from pkg_resources import resource_string as resource_bytes
import genreml.model.cnn.data


class ModelConfig:
    # Total pixels, width, and height for each spectrogram image in FMA dataset
    IMG_PIXELS = 67000
    IMG_WIDTH = 335
    IMG_HEIGHT = 200

    # Number of labels model will be trained to classify
    NUM_LABELS = 32

    # Number of feature extraction parameters
    NUM_FEATURES = 45

    # Training/testing split
    TEST_SPLIT = .2

    # data split random state
    RANDOM_STATE = 42

    # path to FMA datasets
    PATH_TO_FEATURES_DATASET = os.path.join(os.path.dirname(__file__), 'data', 'FMA_features_dataset')
    PATH_TO_IMAGES_DATASET = os.path.join(os.path.dirname(__file__), 'data', 'FMA_images_dataset')

    # get labels from csv file
    LABELS_KEY = pd.read_csv(os.path.join(os.path.dirname(__file__), 'data/labels_key.csv'))['category']

    # set hyperparameters
    BATCH_SIZE = 8
    NUM_EPOCHS = 5
