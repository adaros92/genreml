import os
import sys
import librosa
import pandas as pd
import numpy as np
import multiprocessing as mp
from multiprocessing import Manager
import warnings

NUM_MFCC_COEFF = 20
FMA_LARGE_DIR = '/home/jkinz/Music/fma_large'

def get_columns():
    """ Defines labels for all columns for each data series storing audio data
    String values are appended to columns list then returned.
    Order of values in columns list is important to align with columns in csv file 
    """
    columns = ['track_id']

    #define mean min max and std of spectral stats
    feature_metrics = ['chroma_stft', 'rms', 'spec_cent', 'spec_bw', 'spec_rolloff', 'zcr']
    for f in feature_metrics:
        add_metrics = ['{}-mean'.format(f), '{}-min'.format(f), '{}-max'.format(f),'{}-std'.format(f)]
        columns.extend(add_metrics)
    
    #define mfcc columns
    for i in range(NUM_MFCC_COEFF):
        columns.append('mfcc{}'.format(i))

    return columns

def add_to_series(ds, name, values):
    """ Calculates mean, min, max, and std deviation of each list of values passed to function, 
    then stores value in the data series

    param: pandas.Series ds: Data series that will store audio feature data
    param: string name: name of extracted feature. Must match column header
    param: list values: python list of audio extracted data from librosa 
    """
    # set mean of values 
    ds['{}-mean'.format(name)] = np.mean(values)
    # set min of values 
    ds['{}-min'.format(name)] = np.min(values)
    # set max of values 
    ds['{}-max'.format(name)] = np.max(values)
    # set std of values 
    ds['{}-std'.format(name)] = np.std(values)

def get_features(filepath, filename):
    """ Calls librosa library to extract audio feature data then stores in pandas data series

    :param string path: path to audio file
    :param string fname: name of audio file
    """
    # ignore librosa warning regarding PySoundFile
    warnings.filterwarnings('ignore', module='librosa')

    try:
        # define panda series to hold song data
        ds = pd.Series(index=get_columns(), dtype=np.float32)
        sid = int(filename[:-4])
        ds['track_id'] = sid

        # load audio file
        y, sr = librosa.load('{0}/{1}'.format(filepath, filename))

        #extract specral features
        add_to_series(ds, 'chroma_stft', librosa.feature.chroma_stft(y=y, sr=sr))
        add_to_series(ds, 'rms', librosa.feature.rms(y=y))
        add_to_series(ds, 'spec_cent', librosa.feature.spectral_centroid(y=y, sr=sr))
        add_to_series(ds, 'spec_bw', librosa.feature.spectral_bandwidth(y=y, sr=sr))
        add_to_series(ds, 'spec_rolloff', librosa.feature.spectral_rolloff(y=y, sr=sr))
        add_to_series(ds, 'zcr', librosa.feature.zero_crossing_rate(y))

        # add mfcc spectral coefficients
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=NUM_MFCC_COEFF)
        for count, e in enumerate(mfcc, start=0):
            ds['mfcc{}'.format(count)] = np.mean(e)

    except Exception as e:
        print('ERROR: {}'.format(repr(e)))

    return ds

# get song data from each file in folder, then append to Datafram
def process_thread(ns, path, fname):
    """ Called for each spawned process in thread pool to process each audio file
    Each song's data is stored in pandas data series, which is appended to ns Data Frame

    :param Namespace ns: Data Frame managed by multiprocessing.Manager to allow sharing 
    accress all spawned processes
    :param string path: path to audio file
    :param string fname: name of audio file
    """
    song_ds = get_features(path, fname)
    ns.features = ns.features.append(song_ds, ignore_index=True)
    return fname 

def log_process(fname):
    """ apply_async callback to print feedback message in terminal """
    print('{} complete'.format(fname))

def process_file(file_id, src_path, output_path):
    """ Spanwns pool of CPU threads to loop through each audio file in fma_large/{file_id}
    Data temporarily stored in pandas.DataFrame, then exported to csv file when all files processed
    
    param: string file_id: name of folder inside fma_large directory that is to be processed
    param: string src_path: path to fma_large directory
    param: string output_path: path where features.csv file is located
    """
    file_id = str(file_id).zfill(3)
    path = '{0}/{1}'.format(src_path, file_id)

    # Manager object to hold data of each processed song in pandas Data Frame
    mgr = Manager()
    ns = mgr.Namespace()
    ns.features = pd.DataFrame(columns=get_columns(), dtype=np.float32)

    # multiprocessing package used for multi-threaded processing of audio files
    files = sorted(os.listdir(path))
    pool = mp.Pool(mp.cpu_count())
    for file in files:
        pool.apply_async(process_thread, args=(ns, path, file), callback=log_process)
    pool.close()
    pool.join()
    
    # make sure Dataframe is sorted before exporting to csv
    ns.features = ns.features.sort_values(by=['track_id'])

    # if features.csv doesn't exist, create with headers
    if not os.path.isfile(output_path):
        ns.features.to_csv(output_path, float_format='%.{}e'.format(10), mode='w', index=None)
    else:
        # append data to features.csv file
        ns.features.to_csv(output_path, float_format='%.{}e'.format(10), mode='a', header=False, index=None)


def main(dir_num):
    """ Receives folder number as input (0 thru 155) then extract feature data from each audio file and 
    import to features.csv file. Must define src_directory as local fma_large audio file directory.

    param: int dir_num: input from command line as folder number within fma_large directory
    """
    src_directory = FMA_LARGE_DIR
    dest_path = '../../data/features.csv' 
    assert(int(dir_num) >= 0 and int(dir_num) <= 155)
    process_file(dir_num, src_directory, dest_path)

if __name__ == "__main__":
    main(sys.argv[1])
