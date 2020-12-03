import pkg_resources
from genreml.model.acquisition import extraction
from genreml.model.cnn import cnn, config as model_config
from genreml.model.utils import model_utils, file_handling


def test_local_classification():
    if not file_handling.file_exists(model_config.FMAModelConfig.FMA_MODEL_PATH):
        model_utils.download_model()
    audio_path = pkg_resources.resource_filename('genreml', 'fma_data/000002.mp3')
    model = cnn.CnnModel.from_h5_file(model_config.FMAModelConfig.FMA_MODEL_PATH)
    prediction = model.get_prediction(audio_path)
    file_handling.delete_dir_contents(model_config.FMAModelConfig.FEATURES_PATH)
    assert (len(prediction) == 32)


def test_youtube_classification():
    if not file_handling.file_exists(model_config.FMAModelConfig.FMA_MODEL_PATH):
        model_utils.download_model()
    url = 'https://www.youtube.com/watch?v=yBuub4Xe1mw'
    model = cnn.CnnModel.from_h5_file(model_config.FMAModelConfig.FMA_MODEL_PATH)
    extractor = extraction.SongExtractor()
    extractor.extract(file_path=model_config.FMAModelConfig.TMP_SONG_PATH, yt_url=url)
    audio_path = '{0}.{1}'.format(model_config.FMAModelConfig.TMP_SONG_PATH,
                                  model_config.AudioConfig.AUDIO_FORMAT)
    prediction = model.get_prediction(audio_path)
    file_handling.delete_dir_contents(model_config.FMAModelConfig.FEATURES_PATH)
    file_handling.delete_file(audio_path)
    assert (len(prediction) == 32)
