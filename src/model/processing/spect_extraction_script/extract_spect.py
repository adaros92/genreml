import os
import sys
import librosa
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing as mp
import warnings

FMA_LARGE_DIR = '/home/jkinz/Music/fma_large'
OUTPUT_DIR = '../../data/spect_images/'

def save_to_spectrogram(y, sr, sname):
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
    fig.savefig(OUTPUT_DIR + sname)
    plt.close(fig)


def process_spect(fpath_in, fname_out):
    # ignore librosa warning regarding PySoundFile
    warnings.filterwarnings('ignore', module='librosa')

    try:
        # load mp3 file
        y, sr = librosa.load(fpath_in)

        # convert and save to spectrogram to output file location
        save_to_spectrogram(y, sr, fname_out)

    except Exception as e:
        print('ERROR: {}'.format(repr(e)))

def process_thread(path, fname):
    """ Called for each spawned process in thread pool to process each audio file
    into spectrogram image

    :param string path: path to audio file
    :param string fname: name of audio file
    """
    process_spect('{}/{}'.format(path, fname), fname[:-4])
    return fname 

def log_process(fname):
    """ apply_async callback to print feedback message in terminal """
    print('{} complete'.format(fname))

def process_file(file_id, src_path):
    """ Spanwns pool of CPU threads to loop through each audio file in fma_large/{file_id}
    Data temporarily stored in pandas.DataFrame, then exported to csv file when all files processed
    
    param: string file_id: name of folder inside fma_large directory that is to be processed
    param: string src_path: path to fma_large directory
    """
    file_id = str(file_id).zfill(3)
    path = '{0}/{1}'.format(src_path, file_id)

    # multiprocessing package used for multi-threaded processing of audio files
    files = sorted(os.listdir(path))
    pool = mp.Pool(mp.cpu_count())
    for file in files:
        pool.apply_async(process_thread, args=(path, file), callback=log_process)
    pool.close()
    pool.join()
    

def main(dir_num):
    """ Receives folder number as input (0 thru 155) then extract spectrogram images from each audio file and 
    export to /data/spect_image/{song_id}.png file. Must define src_directory as local fma_large audio file directory.

    param: int dir_num: input from command line as folder number within fma_large directory
    """
    src_directory = FMA_LARGE_DIR
    assert(int(dir_num) >= 0 and int(dir_num) <= 155)
    process_file(dir_num, src_directory)

if __name__ == "__main__":
    main(sys.argv[1])
