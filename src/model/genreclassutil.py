from __future__ import unicode_literals
import re
import subprocess
import urllib.request
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import os
from pydub import AudioSegment

'''
leverages urllib to send a search query to youtube.com
parses the results with re and constructs a list of urls from response
returns url at list index as string
'''
def get_url( songIn, artistIn, index=0):
  #building the request query
  song = re.sub(' ', '+', re.sub(r'[^A-Za-z0-9 ]+', '', songIn))
  artist = re.sub(' ', '+', re.sub(r'[^A-Za-z0-9 ]+', '', artistIn))
  html = urllib.request.urlopen("https://www.youtube.com/results?search_query="
                                + song + "+" + artist)
  #parsing the html
  video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
  return "https://www.youtube.com/watch?v=" + video_ids[index]


'''
downloads wav youtube video url to dl_dir
dl_dir defaults to content/audio/ unless otherwise specified
'''
def download_song (URL, filename, dl_dir="/content/audio/"):
  fo = dl_dir + filename + ".wav"
  test = subprocess.Popen(["youtube-dl", "-f", "bestaudio",
                            "--audio-quality", "0", "--audio-format",
                           "wav", URL, "-o", fo], stdout=subprocess.PIPE)
  output = test.communicate()[0]
  print(output)
  return fo


'''
saves and returns black and white spectogram of audio file to dl_dir
dl_dir defaults to content/img/ unless otherwise specified 
'''
def save_to_spectrogram( y, sr, sname, dl_dir="spectrograms/"):
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
  img = 255-img

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


'''
splits a wav file into n amount of s second clips
n = clip_length / s

'''
def split_by_sec(s, loc, dl_dir="clips/"):
  song = AudioSegment.from_file(loc)
  for i in range(round(song.duration_seconds / s)):
    clip = song[i*s*1000:i*s*1000 + (s*1000)]
    clipname = os.path.basename(loc)
    clipname = clipname[:-4]
    clipname = clipname + "_clip" + str(i) + ".wav"

    script_dir = os.path.dirname(__file__)
    results_dir = os.path.join(script_dir, dl_dir)
    if not os.path.isdir(results_dir):
      os.makedirs(results_dir)

    clip.export(dl_dir+clipname, format="wav")
