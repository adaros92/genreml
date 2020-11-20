from __future__ import unicode_literals
import warnings
import os

warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', module='librosa')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import pickle
import sys
import tempfile
import time
import librosa
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import simpleaudio as sa
import tensorflow as tf
import youtube_dl
from PIL import Image
from scipy.io.wavfile import write
from eyed3 import id3

IMG_PIXELS = 67000
IMG_WIDTH = 335
IMG_HEIGHT = 200
NUM_LABELS = 32
MIN_CLIP_LENGTH = 29
NUM_FEATURES = 44
NUM_MFCC_COEFF = 20
SONG_EXT = 'mp3'
LABELS_DICT = pd.read_csv('./labels_key.csv')['category']
FEATURE_COLS = pd.read_csv('./feature_cols.csv')['feature_columns']


class Song:
    def __init__(self):
        self.path = None
        self.clips = []
        self.features = []
        self.spectrograms = []
        self.sr = None
        self.genre_prediction = []
        self.title = None
        self.artist = None

    def get_predictions(self):
        return self.genre_prediction

    @staticmethod
    def __add_to_series(ds, name, values):
        """ Calculates mean, min, max, and std deviation of each list of values passed to function,
        then stores value in the data series
        :param pandas.Series ds: Data series that will store audio feature data
        :param string name: name of extracted feature. Must match column header
        :param list values: python list of audio extracted data from librosa
        """
        # set mean of values
        ds['{}-mean'.format(name)] = np.mean(values)
        # set min of values
        ds['{}-min'.format(name)] = np.min(values)
        # set max of values
        ds['{}-max'.format(name)] = np.max(values)
        # set std of values
        ds['{}-std'.format(name)] = np.std(values)

    def __get_features(self, source, sr):
        """ Calls librosa library to extract audio feature data then stores in pandas data series
        :param string source: path to audio file
        :param string sr: name of audio file
        """
        # ignore librosa warning regarding PySoundFile
        warnings.filterwarnings('ignore', module='librosa')

        try:
            # define panda series to hold song data
            ds = pd.Series(index=FEATURE_COLS, dtype=np.float32)
            # extract specral features
            self.__add_to_series(ds, 'chroma_stft', librosa.feature.chroma_stft(y=source, sr=sr))
            self.__add_to_series(ds, 'rms', librosa.feature.rms(y=source))
            self.__add_to_series(ds, 'spec_cent', librosa.feature.spectral_centroid(y=source, sr=sr))
            self.__add_to_series(ds, 'spec_bw', librosa.feature.spectral_bandwidth(y=source, sr=sr))
            self.__add_to_series(ds, 'spec_rolloff', librosa.feature.spectral_rolloff(y=source, sr=sr))
            self.__add_to_series(ds, 'zcr', librosa.feature.zero_crossing_rate(source))

            # add mfcc spectral coefficients
            mfcc = librosa.feature.mfcc(y=source, sr=sr, n_mfcc=NUM_MFCC_COEFF)
            for count, e in enumerate(mfcc, start=0):
                ds['mfcc{}'.format(count)] = np.mean(e)

            return ds

        except Exception as e:
            print('ERROR: {}'.format(repr(e)))

    def __extract_features(self, source, sr):
        """ Extract feture data from audio source using genreml
        :param source: raw audio data
        :param sr: sampling rate of audio data
        :returns array of feature data scaled and sorted based on FEATURE_COLS list
        """
        features = self.__get_features(source, sr)
        features_sorted = []
        for col in FEATURE_COLS:
            features_sorted.append(features[col])
        features_sorted = np.array(features_sorted)
        features_sorted = features_sorted[np.newaxis, :]

        # load scaler object from binary exported from trained data
        sc = pickle.load(open('./std_scaler_B.pkl', 'rb'))
        features = sc.transform(features_sorted)[0]
        return features

    @staticmethod
    def __extract_spectrogram(source, sr, output_path, output_name):
        """ Extract spectrogram data from audio source using librosa package
        :param source: raw audio data
        :param sr: sampling rate of audio data
        :param output_path: path to ouput spectrogram image file
        :param output_name: name that will be given to spectrogram image file
        :returns pixel data of spectrogram image generated from audio data
        """
        # generate mel-spectrogram image data from clip
        spect_path = f'{output_path}/img{output_name}'
        mel_spect = librosa.feature.melspectrogram(y=source, sr=sr, n_fft=2048, hop_length=1024)
        mel_spect = librosa.power_to_db(mel_spect, ref=np.max)

        # normalize image between min and max
        img = 255 * ((mel_spect - mel_spect.min()) /
                     (mel_spect.max() - mel_spect.min()))

        # convert pixel values to 8 bit ints
        img = img.astype(np.uint8)

        # flip and invert image
        img = np.flip(img, axis=0)
        img = 255 - img

        # create and export
        fig = plt.figure(frameon=False)
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        ax.imshow(img, aspect='auto', cmap='Greys')
        fig.savefig(spect_path)
        plt.close(fig)

        # open .png file and return raw pixel data
        spect_img = Image.open(f'{spect_path}.png').convert('L')
        spect_img = spect_img.resize((IMG_WIDTH, IMG_HEIGHT))
        spect_img = list(spect_img.getdata())
        return spect_img

    def download_song(self, url, output_path):
        """ Uses youtuble-dl package to download and extrat audio data from youtube url
        :param url: Valid youtuble url
        :param output_path: Output path to store audio file
        """

        def path_hook(d):
            if not self.path:
                file = d['filename'].split('.')[0]
                self.path = f'{file}.{SONG_EXT}'

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path + '/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': SONG_EXT,
                'preferredquality': '192',
                },
                {'key': 'FFmpegMetadata'}
            ],
            'progress_hooks': [path_hook],
            'keepvideo': True
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def play_clips(self):
        """ Function loops through and plays each audio clip from self.clips array
        """
        count = 1
        filename = 'test.wav'
        for clip in self.clips:
            # export wav file
            scaled = np.int16(clip / np.max(np.abs(clip)) * 32767)
            write(filename, self.sr, scaled)
            wave_obj = sa.WaveObject.from_wave_file(filename)

            # play wav file
            print(f'Playing clip #{count}')
            play_obj = wave_obj.play()
            play_obj.wait_done()

            # Wait 2 seconds before playing next clip
            time.sleep(2)
            count += 1

        # delete wav file
        os.remove(filename)

    def extract_song_data(self):
        """ Clips song from raw audio data based on length of song:
        If song greater than 90sec, method will clip three 29sec sections from the middle of the song
        If song less than 90sec, only middle 29sec clip extracted
        If less than 29sec, error is thrown
        """
        y, sr = librosa.load(self.path)
        self.sr = sr

        # length of song in seconds
        length = len(y) / sr

        # assert song length greater than or equal to minimum
        if length < MIN_CLIP_LENGTH:
            raise Exception('Song length too short for accurate prediction')

        # if length of song less than 3 * MIN_CLIP_LENGTH, take middle section
        elif length < MIN_CLIP_LENGTH * 3 + 1:
            mid_index = int(len(y) / 2)
            lower_index = mid_index - int(sr * MIN_CLIP_LENGTH / 2)
            upper_index = lower_index + int(sr * MIN_CLIP_LENGTH)
            self.clips.append(y[lower_index:upper_index])

        # else split song into three clips each at MIN_CLIP_LENGTH in duration
        else:
            num_clips = 3
            mid_index = int(len(y) / 2)
            lower_index = mid_index - int(
                sr * (MIN_CLIP_LENGTH * num_clips / 2))

            for i in range(num_clips):
                upper_index = lower_index + int(sr * MIN_CLIP_LENGTH)
                self.clips.append(y[lower_index:upper_index])
                lower_index = upper_index

        # get song title and artist if avaliable
        tag = id3.Tag()
        tag.parse(self.path)
        self.title = tag.title
        self.artist = tag.artist

    def extract_feature_data(self, spect_output_path: str):
        """ Method to extract feature data and spectrogram image file from each audio clip in self.clips
        :param spect_output_path: Output file path for spectrogram image file
        """
        # loop through each track section and get prediction
        print(f'Extracting data from audio file...')
        count = 1
        for clip in self.clips:
            self.features.append(self.__extract_features(clip, self.sr))
            self.spectrograms.append(self.__extract_spectrogram(clip, self.sr, spect_output_path, count))
            count += 1

    def predict(self):
        """ Prediction method that loops through each clip in self.clips and runs ML prediction model to
        classify song into categories defined in LABELS_DICT
        """
        print(f'Running prediction model...')
        self.genre_prediction = np.array(
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            dtype=np.float64)
        model = tf.keras.models.load_model('FMA_model.h5')
        # model = tf.keras.models.load_model('FMA_model_seperate_genres.h5')
        count = 0
        for image, features in zip(self.spectrograms, self.features):
            count += 1
            # get prediction for each clip and and calculate average
            image = np.array(image).reshape(IMG_HEIGHT, IMG_WIDTH, 1)
            features = np.array(features)
            prediction = model.predict([np.array([features]), np.array([image])])
            self.genre_prediction += prediction[0]

        # calculate average of each clip prediction
        self.genre_prediction = self.genre_prediction / count


def main(dl_type, url_path, n):
    song = Song()
    with tempfile.TemporaryDirectory() as tmp:
        print(f'Created temporary directory: {tmp}')

        try:
            # download song from youtube ('-y') or get local ('-l') file
            if dl_type == '-y':
                song.download_song(url_path, tmp)
            elif dl_type == '-l':
                song.path = url_path
            else:
                raise Exception(
                    'Invalid Input: -y (youtube url) or -l (local file) must be before url or path')

            # extract raw audio data from song and section according to length
            song.extract_song_data()

            # ====== CAREFUL WITH SYSTEM VOLUME!! ======
            # song.play_clips()

            # get feature data and spectrogram images from each clip
            song.extract_feature_data(tmp)

            # get top-n genre prediction
            song.predict()

            # log top-n genres to console
            prediction_arr = song.get_predictions()

            # Log top n predictions to console
            n = int(n)
            top_n_genres = []
            top_n = np.argsort(prediction_arr)
            top_n = top_n[::-1][:n]
            for i, val in enumerate(top_n, start=1):
                top_n_genres.append(LABELS_DICT[val])
            print(f'Top {n} classified genres for ', os.path.splitext(os.path.basename(song.path))[0])
            print(top_n_genres)
            sys.stderr.write(os.path.splitext(os.path.basename(song.path))[0] + ', ' + ', '.join(top_n_genres))

        except Exception as e:
            print('ERROR: {}'.format(repr(e)))
            return


if __name__ == "__main__":
    assert(len(sys.argv) == 4)
    assert(0 < int(sys.argv[3]) < 33)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
