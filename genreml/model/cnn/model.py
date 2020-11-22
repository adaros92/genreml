import pandas as pd
import numpy as np
import os
import pathlib
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Conv2D, MaxPooling2D, Flatten
from tensorflow.keras.optimizers import RMSprop
import pickle
import sys
import math
import logging
import tensorflow as tf
from tensorflow import keras
from genreml.model.cnn.config import ModelConfig
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt


class Model:
    def __init__(self):
        self.images_dataset = []
        self.features_dataset = []
        self.ignore_keys = []
        self.images = []
        self.train_images = []
        self.test_images = []
        self.features = []
        self.train_feat = []
        self.test_feat = []
        self.labels = []
        self.train_labels = []
        self.test_labels = []
        self.track_ids = []
        self.model = None

    def import_data(self):
        try:
            logging.info('Importing datasets')
            self.features_dataset = list(tf.data.experimental.load(ModelConfig.PATH_TO_FEATURES_DATASET, (
                tf.TensorSpec(shape=(ModelConfig.NUM_FEATURES,), dtype=tf.float32, name=None),
                tf.TensorSpec(shape=(ModelConfig.NUM_LABELS,), dtype=tf.int8, name=None))))
            self.images_dataset = list(tf.data.experimental.load(ModelConfig.PATH_TO_IMAGES_DATASET, (
                tf.TensorSpec(shape=(ModelConfig.IMG_PIXELS,), dtype=tf.uint8, name=None),
                tf.TensorSpec(shape=(ModelConfig.NUM_LABELS,), dtype=tf.int8, name=None))))
        except Exception as e:
            logging.error('IMPORT DATASET ERROR: {}'.format(e))
            return

    def set_ignore_categories(self, category_list):
        def get_key(val, obj):
            for key, value in obj.items():
                if val == value:
                    return key

        try:
            # check for valid keys
            for category in category_list:
                if category in ModelConfig.LABELS_KEY.values:
                    continue
                else:
                    raise Exception('Invalid category')

            # if valid categories, add keys to ignore_keys list
            for category in category_list:
                self.ignore_keys.append(get_key(category, ModelConfig.LABELS_KEY))

        except Exception as e:
            logging.error('{}'.format(e))
            return

    def __config_training_data(self):
        for i, (x, y) in enumerate(self.images_dataset):
            label = y.numpy()
            skip = False
            for key in self.ignore_keys:
                if label[key] == 1:
                    skip = True

            # only add data point if not labeled as one of genres in ignore_catories list
            if not skip:
                self.images.append(x.numpy())
                self.features.append(self.features_dataset[i][0][1:].numpy())
                self.labels.append(label)
                self.track_ids.append(self.features_dataset[i][0][0].numpy())

        sc = StandardScaler()
        self.features = sc.fit_transform(np.array(self.features))
        self.images = np.array(self.images)
        self.labels = np.array(self.labels)

        self.images_dataset = None
        self.features_dataset = None

    def __split_training_data(self):
        # define test and train data set
        ts = ModelConfig.TEST_SPLIT
        rs = ModelConfig.RANDOM_STATE
        self.train_images, self.test_images, self.train_labels, self.test_labels = train_test_split(self.images,
                                                                                                    self.labels,
                                                                                                    test_size=ts,
                                                                                                    random_state=rs)
        self.train_feat, self.test_feat, _, _ = train_test_split(self.features,
                                                                 self.labels,
                                                                 test_size=ModelConfig.TEST_SPLIT,
                                                                 random_state=rs)

        # Reshape images to 200x335 pixels
        height = ModelConfig.IMG_HEIGHT
        width = ModelConfig.IMG_WIDTH
        self.train_images = self.train_images.reshape(self.train_images.shape[0], height, width, 1)
        self.test_images = self.test_images.reshape(self.test_images.shape[0], height, width, 1)

        # free memory
        images = None
        features = None
        labels = None

    def display_sample(self, num):
        # Print the one-hot array of this sample's label
        print(self.train_labels[num])
        # Print the label converted back to a number
        label = self.train_labels[num].argmax(axis=0)
        # Reshape the lots of values to a 423x288 image
        image = self.train_images[num].reshape([ModelConfig.IMG_HEIGHT, ModelConfig.IMG_WIDTH])
        plt.title('Sample: %d  Label: %d' % (num, label))
        plt.imshow(image)
        plt.show()

    def build_model(self):
        self.__config_training_data()
        self.__split_training_data()

        img_height = ModelConfig.IMG_HEIGHT
        img_width = ModelConfig.IMG_WIDTH
        input_shape = (img_height, img_width, 1)

        # feature layers
        feat_input = keras.Input(shape=(len(self.train_feat[0]),), name='feat_input')
        x = keras.layers.Dense(512, activation='relu')(feat_input)
        x = keras.layers.Dense(256, activation='relu')(x)
        feat_layers = keras.layers.Dense(128, activation='relu')(x)

        # image convolutional layers
        img_input = keras.Input(shape=input_shape, name="img_input")
        x = tf.cast(img_input, tf.float32)
        x = tf.keras.layers.BatchNormalization()(x)
        x = keras.layers.Conv2D(3, kernel_size=(1, 1), activation='relu')(x)
        x = tf.keras.applications.Xception(include_top=False, input_shape=(img_height, img_width, 3),
                                           weights="imagenet")(x)
        x = tf.keras.layers.GlobalAveragePooling2D()(x)
        img_layers = keras.layers.Dropout(0.25)(x)

        # concatenate img layers with feature layers and define output layer
        combined = keras.layers.concatenate([img_layers, feat_layers])
        out_layer = keras.layers.Dense(32, activation='sigmoid')(combined)

        # define model with both image and feature inputs
        self.model = keras.Model(inputs=[feat_input, img_input], outputs=out_layer)

    def plot_model(self):
        keras.utils.plot_model(self.model, "multi_input_and_output_model.png", show_shapes=True)

    def train_model(self):
        self.model.compile(optimizer='adam', loss=keras.losses.binary_crossentropy, metrics=['accuracy'])
        history = self.model.fit(x=[self.train_feat, self.train_images], y=self.train_labels,
                                 validation_data=([self.test_feat, self.test_images], self.test_labels),
                                 batch_size=ModelConfig.BATCH_SIZE, epochs=ModelConfig.NUM_EPOCHS)

    def get_model_accuracy(self):
        pass

    def export_model(self, output_path):
        pass
