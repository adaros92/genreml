# Name: audio.py
# Description: defines functionality to process audio from audio files

import logging
import librosa
import os
import glob
import json

from model.processing.audio_features import SpectrogramGenerator
from model.processing.config import AudioConfig
from model.utils import file_handling


class AudioFile(object):

    def __init__(self, file_path, audio_signal, sample_rate):
        """ Instantiates an AudioFile object that collects various attributes related to an audio file and exposes
        methods to extract features from that file
        """
        self.file_path = file_path
        self.file_name = file_handling.get_filename(file_path)
        self.audio_type = file_handling.get_filetype(file_path)
        self.audio_signal = audio_signal
        self.sample_rate = sample_rate

    def to_spectrogram(self, destination_filepath, spec_generator=None):
        """ Extract spectrogram from the audio data and save to the destination path

        :param string destination_filepath: the file path to save the spectrogram to
        :param model.processing.audio_features.SpectrogramGenerator spec_generator: option. spectrogram generator to use
        """
        if not spec_generator:
            spec_generator = SpectrogramGenerator(self.audio_signal, self.sample_rate)
        full_path = "{0}spectrogram_{1}".format(destination_filepath, self.file_name.replace(self.audio_type, ""))
        spectrogram = spec_generator.generate()
        spectrogram.savefig(full_path + ".png")
        logging.info("saving spectrogram to {0}".format(full_path + ".png"))
        return full_path + ".png"

    def __repr__(self):
        return "Audio file of type {0} loaded from {1}".format(self.audio_type, self.file_path)

    def __str__(self):
        return self.__repr__()


class AudioFiles(dict):

    def __init__(self):
        """ Instantiates a collection of AudioFile objects represented as a dictionary where each key is the audio
        file's location on disk and each value the corresponding AudioFile object """
        super(AudioFiles, self).__init__()
        self.bad_files_loaded = None
        self.bad_files_extracted = None

    def _load_file(self, file_location):
        """ Reads in a individual file from the given file_location on disk and keeps a record of those files that
        couldn't be read in

        :param string file_location: the path to a file to read in
        """
        self.bad_files_loaded = AudioFiles()
        try:
            logging.info("loading audio file from {0}".format(file_location))
            audio_signal, sample_rate = librosa.load(file_location)
            self[file_location] = AudioFile(file_location, audio_signal, sample_rate)
        except Exception as e:
            logging.warning("failed to load audio file from {0} due to {1}".format(file_location, e))
            self.bad_files_loaded[file_location] = e

    def _extract_features(self, audio_file, file_location, destination_filepath):
        """ Extracts features from a given AudioFile object representing a file in the given file_location and
        saves the features to destination_filepath

        :param AudioFile audio_file: an AudioFile object
        :param string file_location: the path to the file from with the AudioFile object was instantiated
        :param string destination_filepath: the filepath to save the extracted features to
        """
        try:
            logging.info("generating spectrogram")
            audio_file.to_spectrogram(destination_filepath.replace(" ", ""))
            # TODO add other feature extraction here
        except Exception as e:
            logging.warning("failed to extract features from {0} due to {1}".format(file_location, e))
            self.bad_files_extracted[file_location] = e

    def extract_features(self, file_locations, destination_filepath, load=True, audio_format=AudioConfig.AUDIO_FORMAT):
        """ Iterates over all of the files in the file_locations, loads them in to extract audio data, and
        generates features

        :param string file_locations: either the location of a single audio file or directory of files to process
        :param string destination_filepath: the location to save features in
        :param bool load: whether to load the files before extracting the features
        :param string audio_format: the format of the audio files in directory (wav, mp3, etc.)
        """
        self.bad_files_loaded = AudioFiles()
        self.bad_files_extracted = AudioFiles()
        destination_filepath = destination_filepath + AudioConfig.FEATURE_DESTINATION
        file_handling.create_directory(destination_filepath)
        # Only load in and process a single file if the given location a file
        if os.path.isfile(file_locations):
            if load:
                self._load_file(file_locations)
            self._extract_features(self[file_locations], file_locations, destination_filepath)
        # Load in all applicable files if the given location is a directory
        elif os.path.isdir(file_locations):
            logging.info("extracting features from {0} audio files in directory {1}".format(
                audio_format, file_locations))
            if file_locations[-1] == '/':
                file_locations = file_locations[:-1]
            # Retrieve list of files in directory with the matching audio format
            audio_files_in_dir = glob.glob("{0}/*.{1}".format(file_locations, audio_format))
            # Iterate over each file in the directory, load in if applicable, and extract features
            for file in audio_files_in_dir:
                if load:
                    self._load_file(file)
                self._extract_features(self[file], file, destination_filepath)
        else:
            raise RuntimeError("file location {0} given to load audio clips from is invalid".format(file_locations))

        # Record bad files if there was a failure processing any of them
        if len(self.bad_files_extracted) > 0 or len(self.bad_files_loaded) > 0:
            logging.warning("some files couldn't be processed; saved record in {0}".format(destination_filepath))
            self.bad_files_extracted.to_json(destination_filepath + "/files_couldnt_be_extracted.json")
            self.bad_files_loaded.to_json(destination_filepath + "/files_couldnnt_be_loaded.json")

    def to_json(self, filepath):
        """ Serializes self as a json in a given file path

        :param string filepath: the file path to save the JSON to
        """
        with open(filepath, 'w') as outfile:
            json.dump(self, outfile)
