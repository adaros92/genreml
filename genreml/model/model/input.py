

class ModelInput(object):

    def __init__(self, name: str, **kwargs) -> None:
        self.name = name
        for input_name, input_value in kwargs:
            self.__dict__[input_name] = input_value

    def __contains__(self, key: str) -> bool:
        return key in self.__dict__

    def __repr__(self) -> str:
        return "Model input {0}".format(self.name)

    def __str__(self) -> str:
        return self.__repr__()

    def __getitem__(self, item: str) -> any:
        return self.__dict__.get(item)
