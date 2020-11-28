import os

class DatasetConfig:
    # Image pixel size and shape 
    IMG_PIXELS = 67000
    IMG_WIDTH = 335
    IMG_HEIGHT = 200

    # Number of labels model will be trained to classify
    NUM_LABELS = 32

    # Number of feature extraction parameters
    NUM_FEATURES = 45

    # Training/testing split
    TEST_SPLIT = .2

    # categories labels to ignore when building dataset
    IGNORE_CATEGORIES = ['Experimental', 'Spoken', 'Singer-Songwriter']

    # path to tensorflow FMA datasets
    PATH_TO_FEATURES_DATASET = os.path.join(os.path.dirname(__file__), 'data', 'FMA_features_dataset')
    PATH_TO_IMAGES_DATASET = os.path.join(os.path.dirname(__file__), 'data', 'FMA_images_dataset')

    # path to labels csv file
    LABELS_KEY_PATH = os.path.join(os.path.dirname(__file__), 'data/labels_key.csv')
