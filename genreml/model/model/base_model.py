import numpy as np

from abc import ABC, abstractmethod

from genreml.model.model import input


class Model(ABC):

    def __init__(self, name: str) -> None:
        self.name = name
        self.model = None

    @abstractmethod
    def train(self):
        pass

    @abstractmethod
    def predict(self, input_data: input.ModelInput) -> np.array:
        pass
