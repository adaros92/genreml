import pkg_resources
import os

from genreml.model.processing.audio import AudioFiles

AUDIO_FILES_PROCESSOR = AudioFiles()


def test_extract_features():
    """ Tests genreml.model.processing.audio.AudioFiles.extract_features method """
    sample_data_path = pkg_resources.resource_filename('genreml', 'fma_data/')
    AUDIO_FILES_PROCESSOR.extract_sample_fma_features(output_to_file=False)
    files = os.listdir(sample_data_path)
    file_count = len(files)
    assert len(AUDIO_FILES_PROCESSOR.features) == file_count


def test_to_df():
    """ Tests genreml.model.processing.audio.AudioFiles.to_df method """
    df, record_count = AUDIO_FILES_PROCESSOR.to_df()
    assert df.shape[0] == record_count \
        and record_count == len(AUDIO_FILES_PROCESSOR.features)
    assert len(df.columns) == len(AUDIO_FILES_PROCESSOR.features[0])


def test_to_csv():
    """ Tests genreml.model.processing.audio.AudioFiles.to_csv method """
    df, filepath = AUDIO_FILES_PROCESSOR.to_csv("")
    assert df.shape[0] == len(AUDIO_FILES_PROCESSOR.features)
    assert os.path.isfile(filepath)
    os.remove(filepath)


def test_feature_checkpointing():
    """ Tests genreml.model.processing.audio.AudioFiles._checkpoint_feature_extraction method """
    previous_feature_length = len(AUDIO_FILES_PROCESSOR.features)
    AUDIO_FILES_PROCESSOR._checkpoint_feature_extraction("")
    assert len(AUDIO_FILES_PROCESSOR.features_saved) == previous_feature_length
    assert len(AUDIO_FILES_PROCESSOR.features) == 0
