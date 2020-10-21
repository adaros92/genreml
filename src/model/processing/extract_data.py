import os
import sys
import librosa
import pandas as pd
import numpy as np

def get_columns():
    return ('track_id', 'chroma_stft', 'spec_cent', 'spec_bw', 'rolloff', 'zcr')

def get_features(filepath, filename):
    sid = int(filename[:-4])
    y, sr = librosa.load('{0}/{1}'.format(filepath, filename))

    #extract specral features
    chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
    rms = librosa.feature.rms(y=y)
    spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)
    spec_bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    zcr = librosa.feature.zero_crossing_rate(y)
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    data_array = [sid, np.mean(chroma_stft), np.mean(spec_cent), np.mean(spec_bw), np.mean(rolloff), np.mean(zcr)]

    # for val in mfcc:
        # data_array.append(np.mean(val))
    
    return data_array

def process_file(file_id, src_path, output_path):
    file_id = str(file_id).zfill(3)
    path = '{0}/{1}'.format(src_path, file_id)
    song_data = []
    for count, fname in enumerate(sorted(os.listdir(path)), start=1):
        print(fname)
        if (fname != '000002.mp3'):
            break
        song_data.append(get_features(path, fname))

    features = pd.Series(song_data[0], index=get_columns(), dtype=np.float32)
    print(features)

    
    # if features.csv doesn't exist, create with headers
    if not os.path.isfile(output_path):
        features.to_csv(output_path, mode='w')
    else:
        # append data to features.csv file
        features.to_csv(output_path, mode='a', header=False)


def main(dir_num):
    src_directory = '/home/jkinz/Music/fma_large'
    dest_path = '../data/features.csv' 
    assert(int(dir_num) >= 0 and int(dir_num) <= 155)
    process_file(dir_num, src_directory, dest_path)

if __name__ == "__main__":
    main(sys.argv[1])