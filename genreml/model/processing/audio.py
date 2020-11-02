# Name: audio.py
# Description: defines functionality to process audio from audio files

import logging
import librosa
import os
import pkg_resources
import pandas as pd
import glob
import json

from genreml.model.processing.audio_features import SpectrogramGenerator, LibrosaFeatureGenerator
from genreml.model.processing.config import AudioConfig
from genreml.model.utils import file_handling


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
        logging.info("generating spectrogram for {0}".format(self.file_name))
        if not spec_generator:
            spec_generator = SpectrogramGenerator(self.audio_signal, self.sample_rate)
        full_path = "{0}spectrogram_{1}".format(
            destination_filepath, self.file_name.replace(self.audio_type, ""))
        spectrogram = spec_generator.generate()
        spectrogram.savefig(full_path)
        logging.info("saving spectrogram to {0}".format(full_path))
        spec_generator.close_spectrogram(spectrogram)
        return full_path + ".png"

    def extract_features(self,
                         aggregate_features: bool = True,
                         exclude_features: set = None,
                         feature_generator: LibrosaFeatureGenerator = None):
        """ Extract librosa features from the audio data

        :param aggregate_features - whether to aggregate the features extracted or not
        :param exclude_features - an optional set of feature names to exclude from the feature generation
        :param feature_generator - an optional generator to use for generating the features
        :returns a dictionary containing the feature names as keys and the data as values
        """
        logging.info("generating librosa features for {0}".format(self.file_name))
        if not feature_generator:
            feature_generator = LibrosaFeatureGenerator(
                self.audio_signal, self.sample_rate, aggregate_features, exclude_features)
        # Extract features
        features = feature_generator.generate()
        # Append the identifiers for the current audio file to the feature object
        features['file_name'] = self.file_name
        features['file_path'] = self.file_path
        logging.info("generated {0} features for {1}".format(len(features), self.file_name))
        return features

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
        self.features = []
        self.features_saved = []

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

    def _run_feature_extraction(
            self, audio_file, file_location, destination_filepath=None, features_to_exclude=None, output_to_file=True):
        """ Extracts features from a given AudioFile object representing a file in the given file_location and
        saves the features to destination_filepath

        :param AudioFile audio_file: an AudioFile object
        :param string file_location: the path to the file from with the AudioFile object was instantiated
        :param string destination_filepath: the filepath to save the extracted features to
        :param set features_to_exclude: a collection of feature names to exclude from the final result
        :param bool output_to_file: whether to output results to a particular file or not
        """
        if not features_to_exclude:
            features_to_exclude = set()
        try:
            if output_to_file and 'spectrogram' not in features_to_exclude:
                audio_file.to_spectrogram(destination_filepath.replace(" ", ""))
            self.features.append(audio_file.extract_features(exclude_features=features_to_exclude))
        except Exception as e:
            logging.warning("failed to extract features from {0}".format(file_location))
            logging.warning(e)
            self.bad_files_extracted[file_location] = e

    def to_df(self):
        """ Store the list of feature dictionaries in a Pandas dataframe where the keys become the columns

        :returns a pandas data frame representation of the audio features
        """
        df = pd.DataFrame()
        record_count = 0
        for idx, feature_dict in enumerate(self.features):
            record_count += 1
            if idx == 0:
                record_to_insert = {key: [val] for key, val in feature_dict.items()}
                df = pd.DataFrame(record_to_insert)
            else:
                df = df.append(feature_dict, ignore_index=True)
        return df, record_count

    def to_csv(self, destination_filepath: str):
        """ Creates a data frame of the features extracted from the current audio files and saves a CSV representation
        of it to the given filepath

        :param destination_filepath - the path to the directory to save the CSV in
        :returns the data frame of features that was saved as CSV
        """
        df, record_count = self.to_df()
        csv_filepath = "{0}{1}{2}.csv".format(destination_filepath, 'feature_data_', str(os.getpid()))
        if file_handling.file_exists(csv_filepath):
            logging.info(
                "appending feature data frame containing {0} records to {1}".format(record_count, csv_filepath))
            df.to_csv(csv_filepath, float_format='%.{}e'.format(10), header=False, index=None, mode='a')
        else:
            logging.info(
                "writing feature data frame containing {0} records to {1}".format(record_count, csv_filepath))
            df.to_csv(csv_filepath, float_format='%.{}e'.format(10), index=None, mode='w')
        return df, csv_filepath

    def _checkpoint_feature_extraction(self, destination_filepath, clear_features=True):
        logging.info("checkpointing progress to {0}".format(destination_filepath))
        _, _ = self.to_csv(destination_filepath)
        self.features_saved.extend(self.features)
        if clear_features:
            self.features = []

    def extract_features(self,
                         file_locations, destination_filepath=None, features_to_exclude=None,
                         load=True, audio_format=AudioConfig.AUDIO_FORMAT, output_to_file=True):
        """ Iterates over all of the files in the file_locations, loads them in to extract audio data, and
        generates features

        :param string file_locations: either the location of a single audio file or directory of files to process
        :param string destination_filepath: the location to save features in
        :param set features_to_exclude: a collection of feature names to exclude from the final result
        :param bool load: whether to load the files before extracting the features
        :param string audio_format: the format of the audio files in directory (wav, mp3, etc.)
        :param bool output_to_file: whether to output results to a particular file or not
        """
        if output_to_file and not destination_filepath:
            raise ValueError("You must provide a valid destination_filepath to output results")
        self.features, self.features_saved = [], []
        self.bad_files_loaded = AudioFiles()
        self.bad_files_extracted = AudioFiles()
        if output_to_file:
            destination_filepath = destination_filepath + AudioConfig.FEATURE_DESTINATION
            file_handling.create_directory(destination_filepath)
        # Only load in and process a single file if the given location a file
        if os.path.isfile(file_locations):
            if load:
                self._load_file(file_locations)
            self._run_feature_extraction(
                self[file_locations], file_locations, destination_filepath, features_to_exclude, output_to_file)
        # Load in all applicable files if the given location is a directory
        elif os.path.isdir(file_locations):
            logging.info("extracting features from {0} audio files in directory {1}".format(
                audio_format, file_locations))
            if file_locations[-1] == '/':
                file_locations = file_locations[:-1]
            # Retrieve list of files in directory with the matching audio format
            audio_files_in_dir = glob.glob("{0}/*.{1}".format(file_locations, audio_format))
            # Iterate over each file in the directory, load in if applicable, and extract features
            for idx, file in enumerate(audio_files_in_dir):
                if load:
                    self._load_file(file)
                try:
                    self._run_feature_extraction(
                        self[file], file, destination_filepath, features_to_exclude, output_to_file)
                    # Checkpoint features every AudioConfig.CHECKPOINT_FREQUENCY tracks
                    if (idx + 1) % AudioConfig.CHECKPOINT_FREQUENCY == 0 and output_to_file:
                        self._checkpoint_feature_extraction(destination_filepath)
                except Exception as e:
                    logging.critical("could not run feature extraction for {0}".format(file))
                    logging.critical(e)
                    if output_to_file:
                        self._checkpoint_feature_extraction(destination_filepath)
        else:
            raise RuntimeError("file location {0} given to load audio clips from is invalid".format(file_locations))
        if output_to_file:
            self._checkpoint_feature_extraction(destination_filepath)

        # Record bad files if there was a failure processing any of them
        if (len(self.bad_files_extracted) > 0 or len(self.bad_files_loaded) > 0) and output_to_file:
            logging.warning("some files couldn't be processed; saved record in {0}".format(destination_filepath))
            self.bad_files_extracted.to_json(destination_filepath + "/files_couldnt_be_extracted.json")
            self.bad_files_loaded.to_json(destination_filepath + "/files_couldnnt_be_loaded.json")

    def to_json(self, filepath):
        """ Serializes self as a json in a given file path

        :param string filepath: the file path to save the JSON to
        """
        with open(filepath, 'w') as outfile:
            json.dump(self, outfile)

    def extract_sample_fma_features(self, destination_filepath=None, output_to_file=True):
        """ Retrieves audio features from sample FMA audio files packaged with the application in genreml/fma_data

        :param str destination_filepath: the optional path to save features to as part of regular feature extraction
        :param bool output_to_file: whether to save the features in the given destination_filepath or not
        """
        path = pkg_resources.resource_filename('genreml', 'fma_data/')
        self.extract_features(path, destination_filepath=destination_filepath, output_to_file=output_to_file)
