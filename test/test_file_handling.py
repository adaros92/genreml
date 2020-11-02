import os
import pytest

from genreml.model.utils import file_handling


def test_get_directory_path():
    """ Tests genreml.model.utils.file_handling.get_directory_path function """
    # Nominal operation
    base_path = '/Users/JaneDoe/Documents'
    sub_path = '/audio-clips/'
    assert file_handling.get_directory_path(sub_path, base_path) == '/Users/JaneDoe/Documents/audio-clips/'


def test_directory_exists():
    """ Tests genreml.model.utils.file_handling.directory_exists function """
    # Nominal operation
    pid = os.getpid()
    directory_name = './test_dir_exists' + str(pid)
    os.mkdir(directory_name)
    assert file_handling.directory_exists(directory_name)
    os.rmdir(directory_name)
    assert not file_handling.directory_exists(directory_name)


def test_file_exists():
    """ Tests genreml.model.utils.file_handling.file_exists function """
    # Nominal operation
    pid = os.getpid()
    file_name = './test_file' + str(pid)
    with open(file_name, 'w') as f:
        f.write("test file content")
    assert file_handling.file_exists(file_name)
    os.remove(file_name)
    assert not file_handling.file_exists(file_name)


def test_create_directory():
    """ Tests genreml.model.utils.file_handling.create_directory function """
    # Nominal operation
    pid = os.getpid()
    directory_name = './test_dir_create' + str(pid)
    file_handling.create_directory(directory_name)
    assert file_handling.directory_exists(directory_name)
    # Trying to create directory again should do nothing
    file_handling.create_directory(directory_name)
    os.rmdir(directory_name)
    assert not file_handling.directory_exists(directory_name)
    file_handling.create_directory(directory_name)
    assert file_handling.directory_exists(directory_name)
    os.rmdir(directory_name)


def test_get_parent_directory():
    """ Tests genreml.model.utils.file_handling.get_parent_directory function """
    # Nominal operation
    pid = os.getpid()
    base_path = './test_dir_parent'
    sub_path = '/audio-clips{0}/'.format(str(pid))
    file_name = 'some_file.txt'
    full_path = file_handling.get_directory_path(sub_path + file_name, base_path)
    parent_dir_path = file_handling.get_directory_path(sub_path, base_path)
    expected_result = sub_path.split('/')[1]
    file_handling.create_directory(full_path)
    assert file_handling.get_parent_directory(full_path).split('/')[-1] == expected_result
    assert file_handling.get_parent_directory(parent_dir_path).split('/')[-1] == expected_result


def test_get_filename():
    """ Tests genreml.model.utils.file_handling.get_filename function """
    # Nominal operation
    pid = os.getpid()
    base_path = './test_dir_parent'
    sub_path = '/audio-clips{0}/'.format(str(pid))
    file_name = 'some_file.txt'
    full_path = file_handling.get_directory_path(sub_path + file_name, base_path)
    parent_dir_path = file_handling.get_directory_path(sub_path, base_path)
    assert file_handling.get_filename(full_path) == file_name
    # Bad input
    with pytest.raises(ValueError):
        file_handling.get_filename(parent_dir_path)


def test_get_filetype():
    """ Tests genreml.model.utils.file_handling.get_filetype function """
    # Nominal operation
    some_path_1 = "some_path_1/some_file.txt"
    some_path_2 = "some_path_2/some_file.mp3"
    some_path_3 = "some_path_3/some_sub_path_3/"
    assert file_handling.get_filetype(some_path_1) == '.txt'
    assert file_handling.get_filetype(some_path_2) == '.mp3'
    # Bad input
    with pytest.raises(ValueError):
        file_handling.get_filetype(some_path_3)
