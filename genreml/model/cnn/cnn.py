import numpy as np
import tensorflow as tf
from tensorflow import keras

from genreml.model.cnn import config, dataset as ds
from genreml.model.model import base_model, input


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

    def _preprocess_spectrogram(self, image: list) -> np.array:
        """ Reshape pixel data to IMG_HEIGHT x IMG_WIDTH

        :param image: list containing image pixel values as 1D array
        """
        image = np.array(image).reshape(self.config.IMG_HEIGHT, self.config.IMG_WIDTH, 1)
        return image

    def predict(self, input_data: input.ModelInput) -> np.array:
        """ Run model prediction on feature/spectrogram input

        :param input_data: ModelInput object containing input data used for prediction
        """
        if not self.model:
            raise AttributeError("Model {0} is not trained".format(self.name))
        elif "spectrograms" not in input_data or "features" not in input_data:
            raise AttributeError(
                "Both spectrograms and raw features need to be provided to model {0}".format(self.name))
        spectrograms = self._preprocess_spectrogram(input_data["spectrograms"])
        features = np.array(input_data["features"])
        prediction = self.model.predict([np.array([features]), np.array(spectrograms)])
        return prediction

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
