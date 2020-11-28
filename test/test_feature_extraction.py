import glob
import os
import pkg_resources

from genreml.model.processing.audio import AudioFiles, AudioData


def test_extract_features():
    """ Tests genreml.model.processing.audio.AudioFiles.extract_features method and
    genreml.model.processing.audio.AudioData.extract_features method
    """
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
    audio_signal_data = []
    sample_rate_data = []
    for _, audio_obj in audio_files_processor.items():
        audio_signal_data.append(audio_obj.audio_signal)
        sample_rate_data.append(audio_obj.sample_rate)
    audio_data_processor = AudioData(audio_signal_data, sample_rate_data)
    audio_data_processor.extract_features()
    assert len(audio_data_processor.features) == len(audio_files_processor.features_saved)


def test_audio_data():
    """ Tests genreml.model.processing.audio.AudioCollection.audio_data property """
    audio_files_processor = AudioFiles()
    audio_files_processor.extract_sample_fma_features()
    data_count = 0
    for audio_name, audio_signal, sample_rate in audio_files_processor.audio_data:
        data_count += 1
    assert data_count == len(audio_files_processor.features)


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
