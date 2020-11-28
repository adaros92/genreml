from genreml.model.cnn import cnn, dataset as ds
from fma_model_builder import custom_model as cm
from fma_model_builder import dataset_config as config


def build_model():
    # build dataset from tensorflow datasets specified in config file
    dataset = ds.Dataset(config.DatasetConfig)
    # get model from CustomModel object
    keras_model = cm.CustomModel().model
    # train new model
    model = cnn.CnnModel().train_new_model(name='test_model', model=keras_model, dataset=dataset, batch_size=8,
                                           epochs=1, optimizer='adam')
    # export to .h5 file
    model.export_h5()


if __name__ == '__main__':
    build_model()
