import pytest

from genreml.model import __main__


class MockArgs(object):
    """ Args object mimicking ArgParse """
    operation = None
    artist_name = None
    song_name = None
    file_path = None
    example = False
    audio_format = None
    checkpoint_frequency = None
    destination_path = None


def test_validate_args():
    """ Tests genreml.model.__main__.validate_args function """
    # Test nominal download operation
    mock_args = MockArgs()
    mock_args.operation = 'download'
    mock_args.song_name = 'some_song'
    mock_args.artist_name = 'some_artist'
    __main__.validate_args(mock_args)
    # Missing required download attributes
    mock_args.song_name = None
    with pytest.raises(RuntimeError):
        __main__.validate_args(mock_args)
    mock_args.song_name = 'some_song'
    mock_args.artist_name = None
    with pytest.raises(RuntimeError):
        __main__.validate_args(mock_args)
    # Test nominal process operation
    mock_args.operation = 'process'
    mock_args.example = True
    mock_args.destination_path = 'some_path'
    __main__.validate_args(mock_args)
    mock_args.example = False
    mock_args.file_path = 'some_file_path'
    mock_args.destination_path = 'some_path'
    __main__.validate_args(mock_args)
    mock_args.destination_path = None
    __main__.validate_args(mock_args)
    # Missing required process attributes
    mock_args.example = True
    with pytest.raises(RuntimeError):
        __main__.validate_args(mock_args)
    mock_args.example = False
    mock_args.file_path = False
    with pytest.raises(RuntimeError):
        __main__.validate_args(mock_args)
