import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow._api.v2 import data

from genreml.model.cnn import config
from genreml.model.processing import dataset
from genreml.model.model import base_model, input

class CnnInput(input.ModelInput):

    def __init__(self, spectrograms: list, features: list, name: str = "ConvolutionalNeuralNetworkInput") -> None:
        super().__init__(name=name, spectrograms=spectrograms, features=features)


class CnnModel(base_model.Model):

    def __init__(self, name: str = "ConvolutionalNeuralNetwork", model_config=config.CnnModelConfig):
        super().__init__(name)
        self.config = model_config

    def train(self, dataset: dataset.Dataset, batch_size, epochs) -> None:
        # compile model
        self.model.compile(optimizer='adam',
            loss=keras.losses.binary_crossentropy,
            metrics=['accuracy'])

        # train model
        self.training_history = self.model.fit(x=[dataset.train_features, dataset.train_images], y=dataset.train_labels, 
                    validation_data=([dataset.test_features, dataset.test_images], dataset.test_labels), 
                    batch_size=batch_size, epochs=epochs)

    def _preprocess_spectrogram(self, image: list) -> np.array:
        image = np.array(image).reshape(self.config.IMG_HEIGHT, self.config.IMG_WIDTH, 1)
        return image

    def predict(self, input_data: input.ModelInput) -> np.array:
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
        self.model.save(path + self.name + '.h5')


    @classmethod
    def from_h5_file(cls, h5_filepath: str):
        cls_instance = cls()
        cls_instance.model = tf.keras.models.load_model(h5_filepath)
        return cls_instance

    @classmethod
    def train_new_model(cls, name, model, dataset, batch_size, epochs):
        cls_instance = cls(name=name)
        cls_instance.model = model
        cls_instance.train(dataset, batch_size, epochs)
        return cls_instance
