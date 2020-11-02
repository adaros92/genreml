# Name: audio_features.py
# Description: defines how to extract different types of features from audio files

import librosa
import librosa.display
import logging
import matplotlib.pyplot as plt
import numpy as np
import warnings

from abc import ABC, abstractmethod

from genreml.model.processing.config import FeatureExtractorConfig


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


class VisualFeaturesMixin(object):
    """ Defines common functionality for visual feature generation """

    @staticmethod
    def normalize(visual_data: np.array) -> np.array:
        return 255 * ((visual_data - visual_data.min()) /
                      (visual_data.max() - visual_data.min()))

    @staticmethod
    def convert_pixels_to_8_bits(visual_data: np.array) -> np.array:
        return visual_data.astype(np.uint8)

    @staticmethod
    def flip_and_invert(visual_data: np.array) -> np.array:
        flipped_img = np.flip(visual_data, axis=0)
        return 255 - flipped_img

    @staticmethod
    def create_display_figure(frameon: bool = False, display_axes: bool = False,
                              x_axis_name: str = None, y_axis_name: str = None) -> tuple:
        fig = plt.figure(frameon=frameon)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        if not display_axes:
            ax.set_axis_off()
        else:
            ax.set(xlabel=x_axis_name, ylabel=y_axis_name)
        fig.add_axes(ax)
        return fig, ax

    @staticmethod
    def display_data(
            visual_data: np.array, frameon: bool = False, cmap: str = None,
            display_axes: bool = False, x_axis_name: str = None, y_axis_name: str = None) -> plt.figure:
        """ Displays the given data in a matplotlib figure and returns the figure object """
        fig, ax = VisualFeaturesMixin.create_display_figure(frameon, display_axes, x_axis_name, y_axis_name)
        ax.imshow(visual_data, aspect='auto', cmap=cmap)
        return fig

    @staticmethod
    def close_img(fig: plt.figure) -> None:
        """ Closes a matplotlib figure """
        plt.close(fig)


class SpectrogramGenerator(FeatureGenerator, VisualFeaturesMixin):
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
        :returns a numpy array containing the data to plot as a spectrogram
        """
        mel_spect = librosa.feature.melspectrogram(
            y=audio_signal, sr=sample_rate, n_fft=self.config.N_FFT, hop_length=self.config.HOP_LENGTH
        )
        return librosa.power_to_db(mel_spect)

    def _create_spectrogram_data(self, audio_signal: np.ndarray) -> np.ndarray:
        spectrogram_data = np.abs(
            librosa.stft(y=audio_signal, n_fft=self.config.N_FFT, hop_length=self.config.HOP_LENGTH))
        return librosa.amplitude_to_db(spectrogram_data, ref=np.max)

    def generate(self, cmap: str = None) -> plt.figure:
        """ Generates a spectrogram by calling the different component methods of this object

        :param cmap: https://matplotlib.org/3.3.2/api/_as_gen/matplotlib.axes.Axes.imshow.html
        :returns a matplotlib.pyplot.figure object visualizing the spectrogram data
        """
        if self.spectrogram_type == "melspectrogram":
            mel_spect = self._create_db_melspectrogram_data(self.audio_signal, self.sample_rate)
            norm_mel_spect = self.normalize(mel_spect)
            eight_bit_spectrogram = self.convert_pixels_to_8_bits(norm_mel_spect)
            transformed_spectrogram = self.flip_and_invert(eight_bit_spectrogram)
        else:
            spect = self._create_spectrogram_data(self.audio_signal)
            transformed_spectrogram = spect
        return self.display_data(transformed_spectrogram, cmap=cmap)


class WavePlotGenerator(FeatureGenerator, VisualFeaturesMixin):
    """ Generates a waveplot image from audio data

    https://librosa.org/doc/0.7.2/generated/librosa.feature.melspectrogram.html
    https://medium.com/analytics-vidhya/understanding-the-mel-spectrogram-fca2afa2ce53
    """

    def __init__(self, audio_signal: np.ndarray, sample_rate: np.ndarray, config=FeatureExtractorConfig):
        super().__init__(audio_signal, sample_rate, features_to_exclude=None, config=config)

    def generate(self) -> plt.figure:
        """ Generates a wave plot using librosa

        :returns a matplotlib.pyplot.figure object visualizing the wave plot data
        """
        # TODO: this is not adding axes for some reason
        fig, ax = self.create_display_figure(frameon=True, display_axes=True, x_axis_name="Time")
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

    def _extract_features(self) -> dict:
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

    def _aggregate_features(self, feature_dict: dict) -> dict:
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

    def generate(self) -> dict:
        """ Runs the main feature generator logic and returns a dictionary with the processed features

        :returns a dictionary with feature names or aggregations as keys and data/aggregation results as values
        """
        # Extract all of the features in config-based supported features
        features = self._extract_features()
        # If required, aggregate the features extracted
        if self.aggregate_features:
            features = self._aggregate_features(features)
        return features
