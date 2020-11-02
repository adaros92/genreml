# Name: extraction.py
# Description: defines functionality to download audio files from the web

from __future__ import unicode_literals

import youtube_dl
import requests
import logging
import re

from genreml.model.processing.config import YoutubeExtractionConfig, SongExtractorConfig, AudioConfig
from genreml.model.utils import file_handling


class Request(object):

    def __init__(self, base_url):
        """ Instantiates unfiltered request object with just the given URL that will be used to make requests to
        different endpoints

        :param string base_url: the starting URL of the endpoint to use without any filter query parameters
        """
        self.filtered = False
        self.url = base_url

    def filter_by(self, filter_param, filter_value):
        """ Adds request query parameters in the form of ?filter_param=filter_value to the
        existing url

        :param string filter_param: the name of the filter query parameter
        :param string filter_value: the corresponding value of the query parameter
        """
        # The first time this method is called the results will not be filtered
        # The filter should be appended with ?
        if not self.filtered:
            url_format = '{0}?{1}={2}'
            self.filtered = True
        # The subsequent times this method is called, each filter should be appended with &
        else:
            url_format = '{0}&{1}={2}'
        self.url = url_format.format(self.url, filter_param, filter_value)

    def get(self, url=None):
        """ Submits a GET request to an API endpoint

        :param string url: an optional URL to use instead of the one created through constructor
        :returns a response object from the requests library
        """
        if not url:
            url = self.url
        response = requests.get(url)
        # Raise an exception if request is invalid
        response.raise_for_status()
        # Otherwise return the response
        return response


class YouTubeDownloader(object):

    def __init__(self, config=YoutubeExtractionConfig):
        """ Instantiates Youtube downloader with a config object as defined in model.processing.config by default

        :param model.processing.config.YoutubeExtractionConfig config: a Youtube extraction config object
        """
        self.config = config
        config_attributes = config.__dict__
        # Config object must have URLs for retrieving the video IDs from search queries and downloading the actual vids
        assert 'SEARCH_URL' in config_attributes and 'CONTENT_URL' in config_attributes

    def _get_video_id_to_download(self, search_values):
        """ Retrieves a video ID to download based on song and artist search keywords

        :param list search_values: a list of search keywords corresponding to each search parameter in Youtube search
        :returns a single video ID that best matches the given search values
        """
        # There must be as many search values as expected from the config specification
        if len(search_values) != len(self.config.SEARCH_QUERY_PARAMS):
            raise ValueError("The given search filters {0} do not match what's expected: {1}".format(
                search_values, self.config.SEARCH_QUERY_PARAMS))

        # Construct search request to extract YouTube video results
        search_request = Request(self.config.SEARCH_URL)
        for search_param, search_value in zip(self.config.SEARCH_QUERY_PARAMS, search_values):
            search_request.filter_by(search_param, search_value)
        # Get data from search query
        search_response = search_request.get().text
        video_ids = re.findall(r"watch\?v=(\S{11})", search_response)
        # TODO Currently just takes the first match but we may want to add additional parsing logic to pick the best
        result_video_id = video_ids[0]
        return result_video_id

    def download(self, search_values, destination_filepath):
        """ Download a video matching the given search_values to the given destination file path

        :param list search_values: a list of search keywords corresponding to each search parameter in Youtube search
        :param string destination_filepath: the full file path including the file name to download
        """
        # Get the best matching video ID from the given search values
        video_id_to_download = self._get_video_id_to_download(search_values)
        # Create a request object and filter by the video ID extracted above
        content_request = Request(self.config.CONTENT_URL)
        video_filter_param = self.config.CONTENT_QUERY_PARAMS[0]
        content_request.filter_by(video_filter_param, video_id_to_download)
        # Get the full Youtube URL pointing to the best matching video to download
        content_url = content_request.url
        # Download the video to the destination_filepath
        with youtube_dl.YoutubeDL({
            'format': self.config.PREFERRED_AUDIO_QUALITY,
            'outtmpl': destination_filepath,
            'postprocessors': [{
                'key': self.config.POST_PROCESSOR_KEY,
                'preferredcodec': AudioConfig.AUDIO_FORMAT,
                'preferredquality': self.config.POST_PROCESSOR_QUALITY, }]
        }) as ydl:
            ydl.download([content_url])


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
        self.downloader.download([search_query], file_path)
