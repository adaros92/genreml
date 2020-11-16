# Name: audio_features.py
# Description: defines how to extract different types of features from audio files

import librosa
import librosa.display
import logging
import matplotlib.pyplot as plt
import numpy as np
import warnings

from abc import ABC, abstractmethod

from genreml.model.processing.config import FeatureExtractorConfig, DisplayConfig
from genreml.model.processing.display import VisualDataMixin


class FeatureGenerator(ABC):
    """ Abstract feature generation class defines common functionality and interface for all feature generators """

    def __init__(self, audio_signal: np.array, sample_rate: np.array, features_to_exclude: any, config):
        self.audio_signal = audio_signal
        self.sample_rate = sample_rate
        self.features_to_exclude = features_to_exclude
        if not features_to_exclude:
            self.features_to_exclude = set()
        self.config = config

    @abstractmethod
    def generate(self):
        pass


class SpectrogramGenerator(FeatureGenerator, VisualDataMixin):
    """ Generates a spectrogram image from audio data

    https://librosa.org/doc/0.7.2/generated/librosa.feature.melspectrogram.html
    https://medium.com/analytics-vidhya/understanding-the-mel-spectrogram-fca2afa2ce53
    """

    def __init__(self,
                 audio_signal: np.ndarray, sample_rate: np.ndarray,
                 spectrogram_type: str = "melspectrogram", config=FeatureExtractorConfig):
        super().__init__(audio_signal, sample_rate, features_to_exclude=None, config=config)
        self.spectrogram_type = spectrogram_type

    def _create_db_melspectrogram_data(self, audio_signal: np.ndarray, sample_rate: np.ndarray) -> np.ndarray:
        """ Creates the data for a decibel melspectrogram using librosa

        :param audio_signal: an audio time-series
        :param sample_rate: the sampling rate of the audio time-series
        :returns a numpy array containing the data to plot as a melspectrogram
        """
        mel_spect = librosa.feature.melspectrogram(
            y=audio_signal, sr=sample_rate, n_fft=self.config.N_FFT, hop_length=self.config.HOP_LENGTH
        )
        return librosa.power_to_db(mel_spect)

    def _create_db_spectrogram_data(self, audio_signal: np.ndarray) -> np.ndarray:
        """ Creates the data for a decibel spectrogram using librosa

        :param audio_signal: an audio time-series
        :returns a numpy array containing the data to plot as a spectrogram
        """
        spectrogram_data = np.abs(
            librosa.stft(y=audio_signal, n_fft=self.config.N_FFT, hop_length=self.config.HOP_LENGTH))
        return librosa.amplitude_to_db(spectrogram_data, ref=np.max)

    def _create_chromagram_data(self, audio_signal: np.ndarray, sample_rate: np.ndarray) -> np.ndarray:
        """ Generates the data from a chromagram using librosa

        :param audio_signal: an audio time-series
        :param sample_rate: the sampling rate of the audio time-series
        :returns a numpy array containing the data to plot as a chromagram
        """
        chromagram = librosa.feature.chroma_stft(audio_signal, sample_rate, hop_length=self.config.HOP_LENGTH)
        return chromagram

    def generate(self, cmap: str = None,
                 figure_width: float = DisplayConfig.FIGSIZE_WIDTH, figure_height: float = DisplayConfig.FIGSIZE_HEIGHT
                 ) -> plt.figure:
        """ Generates a spectrogram by calling the different component methods of this object

        :param cmap: https://matplotlib.org/3.3.2/api/_as_gen/matplotlib.axes.Axes.imshow.html
        :param figure_width: the spectrogram width in inches
        :param figure_height: the spectrogram height in inches
        :returns a matplotlib.pyplot.figure object visualizing the spectrogram data
        """
        if self.spectrogram_type == "melspectrogram":
            mel_spect = self._create_db_melspectrogram_data(self.audio_signal, self.sample_rate)
            norm_mel_spect = self.normalize(mel_spect)
            eight_bit_spectrogram = self.convert_pixels_to_8_bits(norm_mel_spect)
            transformed_spectrogram = self.flip_and_invert(eight_bit_spectrogram)
        elif self.spectrogram_type == "chromagram":
            chromagram = self._create_chromagram_data(self.audio_signal, self.sample_rate)
            transformed_spectrogram = chromagram
        else:
            spect = self._create_db_spectrogram_data(self.audio_signal)
            transformed_spectrogram = spect
        return self.display_data(
            transformed_spectrogram, cmap=cmap, figure_width=figure_width, figure_height=figure_height)


class WavePlotGenerator(FeatureGenerator, VisualDataMixin):
    """ Generates a waveplot image from audio data

    https://librosa.org/doc/0.7.2/generated/librosa.feature.melspectrogram.html
    https://medium.com/analytics-vidhya/understanding-the-mel-spectrogram-fca2afa2ce53
    """

    def __init__(self, audio_signal: np.ndarray, sample_rate: np.ndarray, config=FeatureExtractorConfig):
        super().__init__(audio_signal, sample_rate, features_to_exclude=None, config=config)

    def generate(self, cmap: str = None,
                 figure_width: float = DisplayConfig.FIGSIZE_WIDTH,
                 figure_height: float = DisplayConfig.FIGSIZE_HEIGHT) -> plt.figure:
        """ Generates a wave plot using librosa

        :param cmap: https://matplotlib.org/3.3.2/api/_as_gen/matplotlib.axes.Axes.imshow.html
        :param figure_width: the waveplot width in inches
        :param figure_height: the waveplot height in inches

        :returns a matplotlib.pyplot.figure object visualizing the wave plot data
        """
        # TODO: this is not adding axes for some reason
        fig, ax = self.create_display_figure(
            frameon=True, display_axes=True, x_axis_name="Time",
            figure_width=figure_width, figure_height=figure_height)
        librosa.display.waveplot(self.audio_signal, self.sample_rate)
        return fig


class LibrosaFeatureGenerator(FeatureGenerator):

    def __init__(self,
                 audio_signal: np.array, sample_rate: np.array, aggregate_features: bool = True,
                 features_to_exclude: list = None, config=FeatureExtractorConfig):
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

    def _extract_features(self) -> tuple:
        """ Extracts the supported features from Librosa and returns the data

        :returns a dictionary containing the names of the features extracted as keys and the data arrays as values
            and a list of feature names in order of processing
        """
        # Define a feature dictionary in which to store feature aggregations
        feature_dict = {}
        feature_names = []
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
                feature_names.append(feature)
            except Exception as e:
                logging.critical("could not extract feature {0}".format(feature))
                raise
        return feature_dict, feature_names

    def _aggregate_features(self, feature_dict: dict) -> tuple:
        """ Aggregates the features in given dictionary of features according to supported aggregations

        :param feature_dict - a dictionary containing feature names to data arrays
        :returns a new dictionary containing the names of the feature aggregations as keys and agg results as values
            and a list of feature names in order of processing
        """
        aggregated_features = {}
        aggregation_functions = {'mean': np.mean, 'min': np.min, 'max': np.max, 'std': np.std}
        feature_names = []
        for feature, data in feature_dict.items():
            # Aggregate the feature data and store the aggregations in the aggregated features dictionary
            if feature != 'mfcc':
                for aggregation in self.aggregations:
                    if aggregation not in aggregation_functions:
                        raise ValueError(
                            "aggregation {0} is not associated with a valid aggregation function".format(aggregation))
                    # Apply the aggregation result and store it
                    aggregation_function = aggregation_functions[aggregation]
                    feature_name = '{0}-{1}'.format(feature, aggregation)
                    aggregated_features[feature_name] = aggregation_function(data)
                    feature_names.append(feature_name)
            else:
                # Other features can't be aggregated
                for mfcc_col in range(self.config.NUMBER_OF_MFCC_COLS):
                    feature_name = 'mfcc{0}'.format(mfcc_col)
                    aggregated_features[feature_name] = aggregation_functions['mean'](data[mfcc_col])
                    feature_names.append(feature_name)
        return aggregated_features, feature_names

    def generate(self) -> tuple:
        """ Runs the main feature generator logic and returns a dictionary with the processed features

        :returns a dictionary with feature names or aggregations as keys and data/aggregation results as values
            and a list of feature names in order of processing
        """
        # Extract all of the features in config-based supported features
        features, feature_names = self._extract_features()
        # If required, aggregate the features extracted
        if self.aggregate_features:
            features, feature_names = self._aggregate_features(features)
        return features, feature_names
