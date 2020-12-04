import numpy as np

from abc import ABC, abstractmethod

from genreml.model.model import input
from genreml.model.cnn import dataset as ds


class Model(ABC):

    def __init__(self, name: str) -> None:
        self.name = name
        self.model = None

    @abstractmethod
    def train(self, dataset: ds.Dataset, batch_size, epochs, optimizer):
        pass

    @abstractmethod
    def _predict(self, input_data: input.ModelInput) -> np.array:
        pass
