# Name: extraction.py
# Description: defines functionality to download audio files from the web

import youtube_dl
import re

from genreml.model.acquisition.config import YoutubeExtractionConfig
from genreml.model.acquisition import request


class YouTubeDownloader(object):

    def __init__(self, config=YoutubeExtractionConfig):
        """ Instantiates Youtube downloader with a config object as defined in model.processing.config by default
        :param model.processing.config.YoutubeExtractionConfig config: a Youtube extraction config object
        """
        self.config = config
        config_attributes = config.__dict__
        # Config object must have URLs for retrieving the video IDs from search queries and downloading the actual vids
        assert 'SEARCH_URL' in config_attributes and 'CONTENT_URL' in config_attributes

    @staticmethod
    def video_id_from_url(video_url: str) -> str:
        """ Extracts the video ID from a Youtube video URL

        :param video_url - the URL to a Youtube video (example - www.youtube.com/watch?v=FDMq9ie0ih0)
        :returns the video ID
        """
        if "v=" not in video_url:
            raise ValueError("Video URL {0} does not contain a valid video ID parameter".format(video_url))
        video_id = video_url.strip("v=")[1]
        return video_id

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
        search_request = request.Request(self.config.SEARCH_URL)
        for search_param, search_value in zip(self.config.SEARCH_QUERY_PARAMS, search_values):
            search_request.filter_by(search_param, search_value)
        # Get data from search query
        search_response = search_request.get().text
        video_ids = re.findall(r"watch\?v=(\S{11})", search_response)
        # TODO Currently just takes the first match but we may want to add additional parsing logic to pick the best
        result_video_id = video_ids[0]
        return result_video_id

    def download(self, destination_filepath: str, search_values: list = None, url: str = None):
        """ Download a video matching the given search_values to the given destination file path
        :param destination_filepath: the full file path including the file name to download
        :param list search_values: a list of search keywords corresponding to each search parameter in Youtube search
        :param url: the content URL to download directly
        """
        content_url = url
        if search_values:
            # Get the best matching video ID from the given search values
            video_id_to_download = self._get_video_id_to_download(search_values)
            # Create a request object and filter by the video ID extracted above
            content_request = request.Request(self.config.CONTENT_URL)
            video_filter_param = self.config.CONTENT_QUERY_PARAMS[0]
            content_request.filter_by(video_filter_param, video_id_to_download)
            # Get the full Youtube URL pointing to the best matching video to download
            content_url = content_request.url
        # Download the video to the destination_filepath
        with youtube_dl.YoutubeDL({
            'format': self.config.PREFERRED_AUDIO_QUALITY,
            'outtmpl': destination_filepath
        }) as ydl:
            ydl.download([content_url])
