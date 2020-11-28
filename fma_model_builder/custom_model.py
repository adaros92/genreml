from tensorflow import keras, cast, float32

IMG_WIDTH = 335
IMG_HEIGHT = 200
NUM_FEATURES = 45

class CustomModel:
    def __init__(self):
        self._build_model()

    def _build_model(self):
        img_height = IMG_HEIGHT
        img_width = IMG_WIDTH
        input_shape = (img_height, img_width, 1)

        # feature layers
        feat_input = keras.Input(shape=(NUM_FEATURES - 1,), name='feat_input')
        x = keras.layers.Dense(512, activation='relu')(feat_input)
        x = keras.layers.Dense(256, activation='relu')(x)
        feat_layers = keras.layers.Dense(128, activation='relu')(x)

        # image convolutional layers
        img_input = keras.Input(shape=input_shape, name="img_input")
        x = cast(img_input, float32)
        x = keras.layers.BatchNormalization()(x)
        x = keras.layers.Conv2D(3, kernel_size=(1, 1), activation='relu')(x)
        x = keras.applications.Xception(include_top=False, input_shape=(img_height, img_width, 3),
                                            weights="imagenet")(x)
        x = keras.layers.GlobalAveragePooling2D()(x)
        img_layers = keras.layers.Dropout(0.25)(x)

        # concatenate img layers with feature layers and define output layer
        combined = keras.layers.concatenate([img_layers, feat_layers])
        out_layer = keras.layers.Dense(32, activation='sigmoid')(combined)

        # define model with both image and feature inputs
        self.model = keras.Model(inputs=[feat_input, img_input], outputs=out_layer)
