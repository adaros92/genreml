import numpy as np
import librosa
import matplotlib.pyplot as plt


class SpectrogramGenerator(object):

    def __init__(self, audio_signal, sample_rate):
        self.audio_signal = audio_signal
        self.sample_rate = sample_rate

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


