# Name: file_handling.py
# Description: defines utility functions to interact with files and directories via the operating system

import os

from pathlib import Path


def get_directory_path(sub_path, base_path=str(Path.home())):
    """ Retrieve the full path that results from concatenating the base_path with the sub_path
     TODO make this more fool-proof and rename

     :param string sub_path: a path to append to the base_path
     :param string base_path: a base_path defaulted to the current machine's home path
     :returns the full concatenated path
    """
    full_path = "{0}{1}".format(base_path, sub_path)
    return full_path


def directory_exists(directory_path):
    """ Checks whether the given path to a directory exists

    :param string directory_path: a file path to a directory
    :returns either True if the directory exists or False otherwise
    """
    return os.path.isdir(directory_path)


def file_exists(filepath: str):
    """ Checks whether the given path to a file exists

    :param filepath: a path to a file
    :returns either True if the file exists or False otherwise
    """
    return os.path.isfile(filepath)


def create_directory(directory_path):
    """ Creates a directory in the given path if it doesn't already exist and opens permissions for the application to
    run successfully

    :param string directory_path: a file path to a directory
    """
    # Check if the directory exists
    if not directory_exists(directory_path):
        # Create it if it doesn't
        os.makedirs(directory_path)
    # Open up permissions to that directory
    os.chmod(directory_path, 0o777)


def get_parent_directory(filepath):
    """ Gets the directory name for a given path; if it's a file then it returns the parent directory and if it's a
    directory then it just returns the same path

    :param string filepath: either a path to a file or directory
    """
    return os.path.dirname(filepath)


def change_directory_to(filepath):
    """ Changes the working directory to the given file path's parent directory

    :param string filepath: a full path to either a file or directory
    """
    # Get the path to the parent directory
    new_path = get_parent_directory(filepath)
    # Change to that new path
    os.chdir(new_path)


def get_filename(filepath):
    """ Extracts the file name from a complete path assuming it's the last item in the path

    :param string filepath: a full path to a file
    :returns the name of the file in the path
    """
    last_item = filepath.split('/')[-1]
    if '.' not in last_item:
        raise ValueError("{0} does not contain a valid file name".format(filepath))
    return last_item


def get_filetype(filepath):
    """ Extracts the type of file from a complete path assuming it's the last item in the path

    :param string filepath: a full path to a file
    :returns the type of the file stored in the path
    """
    file_name = get_filename(filepath)
    return "." + file_name.split(".")[1]
