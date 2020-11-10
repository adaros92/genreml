import glob
import os
import pkg_resources

from genreml.model.processing.audio import AudioFiles


def test_extract_features():
    """ Tests genreml.model.processing.audio.AudioFiles.extract_features method """
    audio_files_processor = AudioFiles()
    sample_data_path = pkg_resources.resource_filename('genreml', 'fma_data/')
    audio_files_processor.extract_sample_fma_features(destination_filepath=os.getcwd())
    files = os.listdir(sample_data_path)
    file_count = len(files)
    assert len(audio_files_processor.features_saved) == file_count
    expected_files = [
        "./features/waveplot*", "./features/melspectrogram*", "./features/chromagram*", "./features/spectrogram*"
    ]
    # There should be as many of the file types above as input file count
    for expected_file in expected_files:
        assert len(glob.glob(expected_file)) == file_count


def test_to_df():
    """ Tests genreml.model.processing.audio.AudioFiles.to_df method """
    audio_files_processor = AudioFiles()
    features = [{"feature_a": 1, "feature_b": 2}, {"feature_a": 2, "feature_b": 3}]
    audio_files_processor.features = features
    df, record_count = audio_files_processor.to_df()
    assert df.shape[0] == record_count \
        and record_count == len(audio_files_processor.features)
    assert len(df.columns) == len(audio_files_processor.features[0])


def test_to_csv():
    """ Tests genreml.model.processing.audio.AudioFiles.to_csv method """
    audio_files_processor = AudioFiles()
    features = {"feature_a": 1, "feature_b": 2}, {"feature_a": 2, "feature_b": 3}
    audio_files_processor.features = features
    df, filepath = audio_files_processor.to_csv("")
    assert df.shape[0] == len(audio_files_processor.features)
    assert os.path.isfile(filepath)
    os.remove(filepath)


def test_feature_checkpointing():
    """ Tests genreml.model.processing.audio.AudioFiles._checkpoint_feature_extraction method """
    audio_files_processor = AudioFiles()
    features = {"feature_a": 1, "feature_b": 2}, {"feature_a": 2, "feature_b": 3}
    audio_files_processor.features = features
    previous_feature_length = len(features)
    audio_files_processor._checkpoint_feature_extraction("")
    assert len(audio_files_processor.features_saved) == previous_feature_length
    assert len(audio_files_processor.features) == 0
