import logging


from genreml.model.acquisition.youtube import YouTubeDownloader
from genreml.model.acquisition.config import SongExtractorConfig
from genreml.model.processing.config import AudioConfig
from genreml.model.utils import file_handling


class SongExtractor(object):

    def __init__(self, source=SongExtractorConfig.SUPPORTED_SOURCES[0], config=SongExtractorConfig):
        """ Instantiates SongExtractor object to interact with downloaders and download audio files from given search
        queries
        :param string source: a supported source to extract audio files from
        :param model.processing.config.SongExtractorConfig config: a SongExtractor config object
        """
        self.config = config

        # The given source must be supported
        if source not in config.SUPPORTED_SOURCES:
            raise ValueError("song source {0} is not one of {1}".format(source, config.SUPPORTED_SOURCES))
        self.source = source
        # Get the associated downloader
        self.downloader = self.get_downloader(source)

    @staticmethod
    def get_downloader(source):
        """ Factory method for different downloaders used by SongExtractor to extract music from the web
        :param string source: the name of the downloader to use (refer to SongExtractorConfig)
        """
        if source == 'youtube':
            return YouTubeDownloader()

    def extract(self, song_name, artist, file_path=None):
        """ Extracts data for the given song name and artist using the active downloader
        :param string song_name: the name of the song to download
        :param string artist: the name of the song's artist
        :param file_path: an optional path to save the song file to (must be an absolute path including the song file)
        """
        # If no full path given, construct one from config
        if not file_path:
            file_path = self.config.DESTINATION_FILEPATH
            full_path = file_handling.get_directory_path(file_path)
            file_handling.create_directory(full_path)
            file_name = '{0}_{1}_clip.{2}'.format(song_name, artist, AudioConfig.AUDIO_FORMAT)
            file_path = "{0}{1}".format(full_path, file_name)
        logging.info("Changing working directory to {0}".format(file_path))
        file_handling.change_directory_to(file_path)
        search_query = '{0}+{1}'.format(song_name, artist)
        self.downloader.download(file_path, search_values=[search_query])
