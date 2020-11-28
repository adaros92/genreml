from genreml.model.cnn import cnn  
from genreml.model.cnn import dataset as ds  
from fma_model_builder import custom_model as cm
from fma_model_builder import dataset_config as config

def build_model():
    dataset = ds.Dataset(config.DatasetConfig)
    keras_model = cm.CustomModel()
    model = cnn.CnnModel().train_new_model(keras_model.model, dataset, batch_size=8, epochs=5)

if __name__ == '__main__':
    build_model()