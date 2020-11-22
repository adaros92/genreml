from __future__ import unicode_literals
import os
import re
import subprocess
import urllib.request

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from pydub import AudioSegment


def get_url(song_in, artist_in, index=0):
    """ Leverages urllib to send a search query to youtube.com
    parses the results with re and constructs a list of urls from response
    returns url at list index as string
    """

    # building the request query
    song = re.sub(' ', '+', re.sub(r'[^A-Za-z0-9 ]+', '', song_in))
    artist = re.sub(' ', '+', re.sub(r'[^A-Za-z0-9 ]+', '', artist_in))
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query="
                                  + song + "+" + artist)
    # parsing the html
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    return "https://www.youtube.com/watch?v=" + video_ids[index]


def download_song(URL, filename, dl_dir="/content/audio/"):
    """ Downloads wav youtube video url to dl_dir
    dl_dir defaults to content/audio/ unless otherwise specified
    """
    fo = dl_dir + filename + ".wav"
    test = subprocess.Popen(["youtube-dl", "-f", "bestaudio",
                             "--audio-quality", "0", "--audio-format",
                             "wav", URL, "-o", fo], stdout=subprocess.PIPE)
    output = test.communicate()[0]
    print(output)
    return fo


def save_to_spectrogram(y, sr, sname, dl_dir="spectrograms/"):
    """ Saves black and white spectogram of audio file to dl_dir
    returns file location
    dl_dir defaults to content/img/ unless otherwise specified
    """

    # create mel scaled spectrogram from input .mp3 file
    mel_spect = librosa.feature.melspectrogram(
        y=y, sr=sr, n_fft=2048, hop_length=1024)
    mel_spect = librosa.power_to_db(mel_spect, ref=np.max)

    # normalize image between min and max
    img = 255 * ((mel_spect - mel_spect.min()) /
                 (mel_spect.max() - mel_spect.min()))

    # convert pixel values to 8 bit ints
    img = img.astype(np.uint8)

    # flip and invert image
    img = np.flip(img, axis=0)
    img = 255 - img

    # create image file and save to current directory
    fig = plt.figure(frameon=False)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    ax.imshow(img, aspect='auto', cmap='Greys')

    script_dir = os.path.dirname(__file__)
    results_dir = os.path.join(script_dir, dl_dir)
    if not os.path.isdir(results_dir):
        os.makedirs(results_dir)

    fig.savefig(dl_dir + sname)

    return (dl_dir + sname + '.png')


def split_by_sec(s, loc, dl_dir="clips/"):
    """splits a wav file into n amount of s second clips
    n = clip_length / s
    """

    song = AudioSegment.from_file(loc)
    for i in range(round(song.duration_seconds / s)):
        clip = song[i * s * 1000:i * s * 1000 + (s * 1000)]
        clipname = os.path.basename(loc)
        clipname = clipname[:-4]
        clipname = clipname + "_clip" + str(i) + ".wav"

        script_dir = os.path.dirname(__file__)
        results_dir = os.path.join(script_dir, dl_dir)
        if not os.path.isdir(results_dir):
            os.makedirs(results_dir)

        clip.export(dl_dir + clipname, format="wav")


def fma_loc_get(sid, dl_dir="./data/fma_full/"):
    """Returns audio file location of a given song id. Intended for use in the FMA dataset
    inputs:
    ddir = data parent directory
    sid = song id
    outputs:
    file location
    """

    sid = str(sid).zfill(6)
    path = dl_dir + sid[0:3] + '/' + sid + '.mp3'
    if os.path.isfile(path):
        return path
    else:
        print('file at ' + path + ' not found')
