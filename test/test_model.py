import pytest

from genreml.model.cnn.model import Model


def test_import_model():
    """ Tests genreml.model.cnn.model functionality """
    test_model = Model()
    test_model.import_data()
    test_model.set_ignore_categories(['Experimental', 'Spoken', 'Singer-Songwriter'])
    test_model.build_model()
    test_model.train_model()
    # test_model.display_sample(123)
    return


if __name__ == '__main__':
    test_import_model()
