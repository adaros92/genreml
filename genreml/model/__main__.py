import argparse
import logging

from genreml.model.processing import extraction, audio, config
from genreml.model.utils import string_parsing, file_handling, logger


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
    parser.add_argument('-a', '--artist_name', help='the name of song\'s artist')
    parser.add_argument('-fp', '--file_path', help='the file path of an audio clip or directory of clips to process')
    parser.add_argument('-e', '--exclude_features', help='a list of feature names to exclude from processing')
    parser.add_argument(
        '-af', '--audio_format', default=config.AudioConfig.AUDIO_FORMAT, help='the format of the audio to process')
    parser.add_argument(
        '-cf', '--checkpoint_frequency', default=config.AudioConfig.CHECKPOINT_FREQUENCY,
        help='how many tracks to process before saving features'
    )
    return parser.parse_args()


def validate_args(args):
    """ Validates the arguments passed in via the CLI """
    if args.operation == 'download' and not (args.song_name and args.artist_name):
        raise RuntimeError('both the song name and artist must be provided to download a clip')
    elif args.operation == 'process' and not args.file_path:
        raise RuntimeError(
            'you must either pass in a path to an audio file to process or a path to a directory with audio files')


def set_config(args):
    """ Sets any config attributes provided through CLI """
    # Set the audio format to use in processing
    config.AudioConfig.AUDIO_FORMAT = args.audio_format
    # Set the checkpointing frequency in number of tracks processed
    config.AudioConfig.CHECKPOINT_FREQUENCY = args.checkpoint_frequency


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
        features_to_exclude = string_parsing.str_to_collection(args.exclude_features, set)
        processor.extract_features(args.file_path, feature_destination_path, features_to_exclude=features_to_exclude)


def main():
    # Step 1: parse the arguments passed in via the CLI
    args = parse_args()
    # Step 2: validates that the arguments passed in are correct; throws exception if not the case
    validate_args(args)
    # Step 3: Set the config with any eligible inputs to update configs with
    set_config(args)
    # Step 4: Set up logger
    logger.setup_logger()
    # Step 5: run the operation
    run(args)


if __name__ == '__main__':
    main()
