# Name: audio_features.py
# Description: defines how to extract different types of features from audio files

import librosa
import logging
import matplotlib.pyplot as plt
import numpy as np
import warnings

from abc import ABC, abstractmethod

from model.processing.config import FeatureExtractorConfig


class FeatureGenerator(ABC):
    """ Abstract feature generation class defines common functionality and interface for all feature generators """

    def __init__(self, audio_signal, sample_rate, features_to_exclude, config):
        self.audio_signal = audio_signal
        self.sample_rate = sample_rate
        self.features_to_exclude = features_to_exclude
        if not features_to_exclude:
            self.features_to_exclude = set()
        self.config = config

    @abstractmethod
    def generate(self):
        pass


class SpectrogramGenerator(FeatureGenerator):

    def __init__(self, audio_signal, sample_rate, config=FeatureExtractorConfig):
        super().__init__(audio_signal, sample_rate, features_to_exclude=None, config=config)

    @staticmethod
    def normalize_spectrogram(db_mel_spect):
        return 255 * ((db_mel_spect - db_mel_spect.min()) /
               (db_mel_spect.max() - db_mel_spect.min()))

    @staticmethod
    def convert_pixels_to_8_bit_ints(spectrogram_img):
        return spectrogram_img.astype(np.uint8)

    @staticmethod
    def flip_and_invert_spectrogram(spectrogram_img):
        img = np.flip(spectrogram_img, axis=0)
        return 255 - img

    @staticmethod
    def create_db_mel_spectrogram(audio_signal, sample_rate):
        mel_spect = librosa.feature.melspectrogram(
            y=audio_signal, sr=sample_rate, n_fft=2048, hop_length=1024
        )
        return librosa.power_to_db(mel_spect)

    @staticmethod
    def create_matplot_spectrogram(spectrogram_img):
        fig = plt.figure(frameon=False)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        ax.imshow(spectrogram_img, aspect='auto', cmap='Greys')
        return fig

    def generate(self):
        mel_spect = self.create_db_mel_spectrogram(self.audio_signal, self.sample_rate)
        norm_mel_spect = self.normalize_spectrogram(mel_spect)
        eight_bit_spectrogram = self.convert_pixels_to_8_bit_ints(norm_mel_spect)
        transformed_spectrogram = self.flip_and_invert_spectrogram(eight_bit_spectrogram)
        return self.create_matplot_spectrogram(transformed_spectrogram)


class LibrosaFeatureGenerator(FeatureGenerator):

    def __init__(self,
                 audio_signal, sample_rate, aggregate_features: bool = True,
                 features_to_exclude=None, config=FeatureExtractorConfig):
        """ Constructor capturing the raw audio_signal and sample_rate data extracted from librosa audio processing
        to generate features from that data
        """
        super().__init__(audio_signal, sample_rate, features_to_exclude, config)
        # Ignore Librosa warning regarding PySoundFile
        warnings.filterwarnings('ignore', module='librosa')
        self.aggregate_features = aggregate_features
        self.supported_features = self.config.SUPPORTED_FEATURES
        self.aggregations = self.config.FEATURE_AGGREGATION

    def _get_feature_function(self, feature: str):
        """ Factory method for librosa function corresponding to a given feature name

        :param feature - the name of the feature for which to retrieve the librosa function
        :returns the librosa function object and inputs it requires to generate the given feature name
        """
        # Some librosa functions require both audio signal and sample rate, some just audio signal, etc.
        input_types = [
            {'y': self.audio_signal, 'sr': self.sample_rate},
            {'y': self.audio_signal},
            {'y': self.audio_signal, 'sr': self.sample_rate, 'n_mfcc': self.config.NUMBER_OF_MFCC_COLS},
        ]
        features = {
            'chroma_stft': (librosa.feature.chroma_stft, input_types[0]),
            'rms': (librosa.feature.rms, input_types[1]),
            'spec_cent': (librosa.feature.spectral_centroid, input_types[0]),
            'spec_bw': (librosa.feature.spectral_bandwidth, input_types[0]),
            'spec_rolloff': (librosa.feature.spectral_rolloff, input_types[0]),
            'zcr': (librosa.feature.zero_crossing_rate, input_types[1]),
            'mfcc': (librosa.feature.mfcc, input_types[2])
        }
        try:
            return features[feature]
        except KeyError:
            logging.critical("feature {0} is not associated with a librosa feature function".format(feature))

    def _extract_features(self):
        """ Extracts the supported features from Librosa and returns the data

        :returns a dictionary containing the names of the features extracted as keys and the data arrays as values
        """
        # Define a feature dictionary in which to store feature aggregations
        feature_dict = {}
        for feature in self.supported_features:
            # Skip feature generation for any features that need to be excluded
            if feature in self.features_to_exclude:
                continue
            try:
                # Get the function and inputs to use for the given feature
                librosa_function, inputs = self._get_feature_function(feature)
                # Extract the feature data
                feature_data = librosa_function(**inputs)
                feature_dict[feature] = feature_data
            except Exception as e:
                logging.critical("could not extract feature {0}".format(feature))
                raise
        return feature_dict

    def _aggregate_features(self, feature_dict: dict):
        """ Aggregates the features in given dictionary of features according to supported aggregations

        :param feature_dict - a dictionary containing feature names to data arrays
        :returns a new dictionary containing the names of the feature aggregations as keys and agg results as values
        """
        aggregated_features = {}
        aggregation_functions = {'mean': np.mean, 'min': np.min, 'max': np.max, 'std': np.std}
        for feature_name, data in feature_dict.items():
            # Aggregate the feature data and store the aggregations in the aggregated features dictionary
            if feature_name != 'mfcc':
                for aggregation in self.aggregations:
                    if aggregation not in aggregation_functions:
                        raise ValueError(
                            "aggregation {0} is not associated with a valid aggregation function".format(aggregation))
                    # Apply the aggregation result and store it
                    aggregation_function = aggregation_functions[aggregation]
                    aggregated_features['{0}-{1}'.format(feature_name, aggregation)] = aggregation_function(data)
            else:
                # Other features can't be aggregated
                for mfcc_col in range(self.config.NUMBER_OF_MFCC_COLS):
                    aggregated_features['mfcc{0}'.format(mfcc_col)] = aggregation_functions['mean'](data)
        return aggregated_features

    def generate(self):
        """ Runs the main feature generator logic and returns a dictionary with the processed features

        :returns a dictionary with feature names or aggregations as keys and data/aggregation results as values
        """
        # Extract all of the features in config-based supported features
        features = self._extract_features()
        # If required, aggregate the features extracted
        if self.aggregate_features:
            features = self._aggregate_features(features)
        return features
