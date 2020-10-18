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


def change_directory_to(filepath):
    """ Changes the working directory to the given file path's parent directory

    :param string filepath: a full path to either a file or directory
    """
    # Get the path to the parent directory
    new_path = os.path.dirname(filepath)
    # Change to that new path
    os.chdir(new_path)
