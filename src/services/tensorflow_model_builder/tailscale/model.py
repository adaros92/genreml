import keras
from keras import models
from keras import layers as keras_layers
import asyncio


event_loop = asyncio.get_event_loop()


async def build_model(layers=None, epochs=None, batch_size=None, X_train=None, y_train=None, X_test=None, y_test=None):
    if layers is None or epochs is None or batch_size is None or X_train is None or y_train is None:
        return (None, (None, None))
    try:
        model = models.Sequential()
        model.add(keras_layers.Dense(layers, activation='relu', input_shape=(X_train.shape[1],)))
        model.add(keras_layers.Dense(10, activation='softmax'))
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        model.fit(
            X_train,
            y_train,
            epochs=epochs,
            batch_size=batch_size,
            verbose=0
        )
        results = None
        if X_test is not None and y_test is not None:
            results = model.evaluate(X_test, y_test, verbose=0)
        return (True, (model, results))
    except Exception as ex:
        return (False, (ex, None))
    return (None, (None, None))
