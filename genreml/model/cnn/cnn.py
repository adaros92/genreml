import os
import numpy as np
import pandas as pd
import pickle
from PIL import Image

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
from tensorflow import keras

from genreml.model.processing import audio, config
from genreml.model.cnn import config, dataset as ds
from genreml.model.model import base_model, input
from genreml.model.utils import file_handling


class CnnInput(input.ModelInput):

    def __init__(self, spectrograms: list, features: list, name: str = "ConvolutionalNeuralNetworkInput") -> None:
        super().__init__(name=name, spectrograms=spectrograms, features=features)


class CnnModel(base_model.Model):
    """Model class that contains keras model built from .h5 file or custom model trained with FMA dataset"""

    def __init__(self, name: str = "ConvolutionalNeuralNetwork", model_config=config.CnnModelConfig):
        super().__init__(name)
        self.config = model_config
        self.training_history = None

    def train(self, dataset: ds.Dataset, batch_size, epochs, optimizer) -> None:
        """ Train keras model against FMA dataset passed to function

        :param dataset: FMA dataset object
        :param batch_size: batch size used during model training
        :param epochs: number of epochs to train model
        :param optimizer: optimizer used to train model
        """

        # compile model
        self.model.compile(optimizer=optimizer,
                           loss=keras.losses.binary_crossentropy,
                           metrics=['accuracy'])

        # train model
        self.training_history = self.model.fit(x=[dataset.train_features, dataset.train_images], y=dataset.train_labels,
                                               validation_data=(
                                                   [dataset.test_features, dataset.test_images], dataset.test_labels),
                                               batch_size=batch_size, epochs=epochs)

    @staticmethod
    def _process_features(features: dict):
        """ Extract feture data from audio source using genreml
        :param features: feature data dictionary
        :returns array of feature data scaled and sorted based on FEATURE_COLS list
        """
        features_sorted = []
        feature_cols = pd.read_csv(config.FMAModelConfig.FEATURE_COLS)['feature_columns']
        for col in feature_cols:
            features_sorted.append(features[col])
        features_sorted = np.array(features_sorted)
        features_sorted = features_sorted[np.newaxis, :]

        # load scaler object from binary exported from trained data
        sc = pickle.load(open(config.FMAModelConfig.PKL_PATH, 'rb'))
        features = sc.transform(features_sorted)[0]
        return features

    def _preprocess_spectrogram(self, image: list) -> np.array:
        """ Reshape pixel data to IMG_HEIGHT x IMG_WIDTH

        :param image: list containing image pixel values as 1D array
        """
        image = np.array(image).reshape(self.config.IMG_HEIGHT, self.config.IMG_WIDTH, 1)
        return image

    def _predict(self, input_data: input.ModelInput) -> np.array:
        """ Run model prediction on feature/spectrogram input

        :param input_data: ModelInput object containing input data used for prediction
        """
        if not self.model:
            raise AttributeError("Model {0} is not trained".format(self.name))
        elif "spectrograms" not in input_data or "features" not in input_data:
            raise AttributeError(
                "Both spectrograms and raw features need to be provided to model {0}".format(self.name))
        spectrogram = self._preprocess_spectrogram(input_data["spectrograms"])
        features = self._process_features(input_data["features"])
        features = np.array(features)
        prediction = self.model.predict([np.array([features]), np.array([spectrogram])])

        return prediction

    def get_prediction(self, audio_path):
        """ Method used to get prediction results

        :param string audio_path: local path to audio file that will be used for the prediction
        """
        # extract data from audio file
        audio_files = audio.AudioFiles()
        output_path = config.FMAModelConfig.SPECT_IMG_PATH
        audio_files.extract_features(file_locations=audio_path,
                                     destination_filepath=output_path,
                                     features_to_exclude={'spectrogram', 'chromagram', 'waveplot'},
                                     figure_height=config.CnnModelConfig.IMG_HEIGHT / 100,
                                     figure_width=config.CnnModelConfig.IMG_WIDTH / 100)

        # # open .png file and return raw pixel data
        path = audio_files.visual_paths[0][0]
        spect_img = Image.open(path).convert('L')
        spect_img = spect_img.resize((config.CnnModelConfig.IMG_WIDTH, config.CnnModelConfig.IMG_HEIGHT))
        spect_img = list(spect_img.getdata())

        # build model input object
        input_obj = CnnInput(spectrograms=spect_img, features=audio_files.features_saved[0])

        # run model prediction
        prediction = self._predict(input_data=input_obj)

        file_handling.delete_dir_contents(config.FMAModelConfig.FEATURES_PATH)
        return prediction[0]

    def export_h5(self, path='./'):
        """ Export keras model to .h5 file at path location

        :param path: path to local directory to store .h5 file
        """
        self.model.save(path + self.name + '.h5')

    @classmethod
    def from_h5_file(cls, h5_filepath: str):
        """ Instantiate CnnModel object from local .h5 file

        :param h5_filepath: local file path to .h5 file
        """
        cls_instance = cls()
        cls_instance.model = tf.keras.models.load_model(h5_filepath)
        return cls_instance

    @classmethod
    def train_new_model(cls, name, model, dataset, batch_size, epochs, optimizer):
        """ Instantiate CnnModel object by training keras model

        :param name: model name
        :param model: keras model to be trained
        :param dataset: dataset used to train model
        :param batch_size: batch_size used during model training
        :param epochs: number of epochs used to train model
        :param optimizer: optimizer used to train model
        """
        cls_instance = cls(name=name)
        cls_instance.model = model
        cls_instance.train(dataset, batch_size, epochs, optimizer)
        return cls_instance
