import logging
import tensorflow as tf
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


class Dataset:
    """ Dataset class builds data needed for model training as specified in config file passed when instance created
    Config file must include the following:

    IMG_PIXELS - number of pixel images
    IMG_WIDTH - image pixel width
    IMG_HEIGHT - image pixel height
    NUM_LABELS - number of output labels
    NUM_FEATURES - number of extracted features in features_dataset (including track id)
    TEST_SPLIT - train/test split for model training
    IGNORE_CATEGORIES - song labels to be ignored
    PATH_TO_FEATURES_DATASET - path to features tensorflow dataset
    PATH_TO_IMAGES_DATASET - path to images tensforflow dataset
    LABELS_KEY_PATH - path to labels.csv file
    """
    def __init__(self, dataset_config):
        self.config = dataset_config
        self._features_dataset = None
        self._images_dataset = None
        self._ignore_keys = []
        self._features = []
        self._images = []
        self._labels = []

        self.train_images = []
        self.train_features = []
        self.train_labels = []
        self.test_images = []
        self.test_features = []
        self.test_labels = []
        self.track_ids = []

        self._build()

    def _import_data(self):
        # import tensorflow datasets
        try:
            logging.info('Importing tensorflow datasets')
            self._features_dataset = list(tf.data.experimental.load(self.config.PATH_TO_FEATURES_DATASET, (
                tf.TensorSpec(shape=(self.config.NUM_FEATURES,), dtype=tf.float32, name=None),
                tf.TensorSpec(shape=(self.config.NUM_LABELS,), dtype=tf.int8, name=None))))
            self._images_dataset = list(tf.data.experimental.load(self.config.PATH_TO_IMAGES_DATASET, (
                tf.TensorSpec(shape=(self.config.IMG_PIXELS,), dtype=tf.uint8, name=None),
                tf.TensorSpec(shape=(self.config.NUM_LABELS,), dtype=tf.int8, name=None))))
        except Exception as e:
            logging.error('IMPORT DATASET ERROR: {}'.format(e))
            return

    def _set_ignore_categories(self):
        # remove data with categories listed in IGNORE_CATEGORIES array
        category_list = self.config.IGNORE_CATEGORIES
        labels_key = pd.read_csv(self.config.LABELS_KEY_PATH)['category']

        def get_key(val, obj):
            for key, value in obj.items():
                if val == value:
                    return key

        try:
            # check for valid keys
            for category in category_list:
                if category in labels_key.values:
                    continue
                else:
                    raise Exception('Invalid category')

            # if valid categories, add keys to ignore_keys list
            for category in category_list:
                self._ignore_keys.append(get_key(category, labels_key))

        except Exception as e:
            logging.error('{}'.format(e))
            return

    def _config_training_data(self):
        # configure dataset for model training
        for i, (x, y) in enumerate(self._images_dataset):
            label = y.numpy()
            skip = False
            for key in self._ignore_keys:
                if label[key] == 1:
                    skip = True

            # only add data point if not labeled as one of genres in ignore_catories list
            if not skip:
                self._images.append(x.numpy())
                self._features.append(self._features_dataset[i][0][1:].numpy())
                self._labels.append(label)
                self.track_ids.append(self._features_dataset[i][0][0].numpy())

        sc = StandardScaler()
        self._features = sc.fit_transform(np.array(self._features))
        self._images = np.array(self._images)
        self._labels = np.array(self._labels)

        self._images_dataset = None
        self._features_dataset = None

    def _split_training_data(self):
        # define test and train data set
        ts = self.config.TEST_SPLIT
        self.train_images, self.test_images, self.train_labels, self.test_labels = train_test_split(self._images,
                                                                                                    self._labels,
                                                                                                    test_size=ts,
                                                                                                    random_state=42)
        self.train_features, self.test_features, _, _ = train_test_split(self._features,
                                                                         self._labels,
                                                                         test_size=self.config.TEST_SPLIT,
                                                                         random_state=42)

        # Reshape images to 200x335 pixels
        height = self.config.IMG_HEIGHT
        width = self.config.IMG_WIDTH
        self.train_images = self.train_images.reshape(self.train_images.shape[0], height, width, 1)
        self.test_images = self.test_images.reshape(self.test_images.shape[0], height, width, 1)

        self._images = None
        self._features = None
        self._labels = None

    def _build(self):
        # build runner that is triggered when instance is created
        logging.info('Building dataset for model training')
        self._import_data()
        self._set_ignore_categories()
        self._config_training_data()
        self._split_training_data()
        logging.info('Dataset finished building')
