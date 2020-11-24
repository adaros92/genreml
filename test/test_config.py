from genreml.model.processing import config as processing_config
from genreml.model.acquisition import config as acquisition_config


def test_audio_config():
    """ Tests that genreml.model.processing.config.AudioConfig has all the required attributes """
    checkpoint_frequency = processing_config.AudioConfig.CHECKPOINT_FREQUENCY
    audio_format = processing_config.AudioConfig.AUDIO_FORMAT
    feature_destination = processing_config.AudioConfig.FEATURE_DESTINATION
    assert checkpoint_frequency and audio_format and feature_destination


def test_youtube_extractor_config():
    """ Tests that genreml.model.processing.config.YoutubeExtractorConfig has all the required attributes """
    post_processor_quality = acquisition_config.YoutubeExtractionConfig.POST_PROCESSOR_QUALITY
    post_processor_key = acquisition_config.YoutubeExtractionConfig.POST_PROCESSOR_KEY
    preferred_audio_quality = acquisition_config.YoutubeExtractionConfig.PREFERRED_AUDIO_QUALITY
    content_query_params = acquisition_config.YoutubeExtractionConfig.CONTENT_QUERY_PARAMS
    content_url = acquisition_config.YoutubeExtractionConfig.CONTENT_URL
    search_query_params = acquisition_config.YoutubeExtractionConfig.SEARCH_QUERY_PARAMS
    search_url = acquisition_config.YoutubeExtractionConfig.SEARCH_URL
    assert search_url and search_query_params and content_url and content_query_params and preferred_audio_quality \
        and post_processor_key and post_processor_quality and preferred_audio_quality


def test_song_extractor_config():
    """ Tests that genreml.model.processing.config.SongExtractorConfig has all the required attributes """
    supported_sources = acquisition_config.SongExtractorConfig.SUPPORTED_SOURCES
    destination_filepath = acquisition_config.SongExtractorConfig.DESTINATION_FILEPATH
    assert supported_sources and destination_filepath


def test_feature_extractor_config():
    """ Tests that genreml.model.processing.config.FeatureExtractorConfig has all the required attributes """
    mfcc_cols = processing_config.FeatureExtractorConfig.NUMBER_OF_MFCC_COLS
    feature_aggregation = processing_config.FeatureExtractorConfig.FEATURE_AGGREGATION
    supported_features = processing_config.FeatureExtractorConfig.SUPPORTED_FEATURES
    assert mfcc_cols and feature_aggregation and supported_features
