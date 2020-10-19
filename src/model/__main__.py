import argparse
import logging

from model.processing import extraction, audio
from model.utils import file_handling


def setup_logger():
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')


def parse_args():
    """ Parse arguments passed in via the CLI

    :returns a parsed argument object from argparse
    """
    parser = argparse.ArgumentParser()
    # Accept the operation to perform
    parser.add_argument('operation', choices=['download', 'process'], help='''the operation to perform:
    download - search for and download an audio clip for the given song name and artist  
    process - extract data from an audio clip stored in a given file path
    ''')
    parser.add_argument('-s', '--song_name', help='the name of the song to download')
    parser.add_argument('-a', '--artist_name', help = 'the name of song\'s artist')
    parser.add_argument('-fp', '--file_path', help='the file path of an audio clip or directory of clips to process')
    return parser.parse_args()


def validate_args(args):
    """ Validates the arguments passed in via the CLI """
    if args.operation == 'download' and not (args.song_name and args.artist_name):
        raise RuntimeError('both the song name and artist must be provided to download a clip')
    elif args.operation == 'process' and not args.file_path:
        raise RuntimeError(
            'you must either pass in a path to an audio file to process or a path to a directory with audio files')


def run(args):
    """ Run the operation as specified via CLI argument """
    # Download clips
    if args.operation == 'download':
        extractor = extraction.SongExtractor()
        extractor.extract(args.song_name, args.artist_name)
    # Extract features from clips
    elif args.operation == 'process':
        processor = audio.AudioFiles()
        feature_destination_path = file_handling.get_parent_directory(args.file_path)
        processor.extract_features(args.file_path, feature_destination_path)


def main():
    # Step 1: Set up logger
    setup_logger()
    # Step 2: parse the arguments passed in via the CLI
    args = parse_args()
    # Step 3: validates that the arguments passed in are correct; throws exception if not the case
    validate_args(args)
    # Step 4: run the operation
    run(args)


if __name__ == '__main__':
    main()
