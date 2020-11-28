class YoutubeExtractionConfig:
    # URL to make request to for audio results
    SEARCH_URL = 'https://www.youtube.com/results'
    # Query parameters to filter requests to search URL by
    SEARCH_QUERY_PARAMS = ['search_query']
    # URL to make request to for actual audio data
    CONTENT_URL = 'https://www.youtube.com/watch'
    # Query parameters to filter requests to content URL by
    CONTENT_QUERY_PARAMS = ['v']
    # Post-processor key to use
    POST_PROCESSOR_KEY = 'FFmpegExtractAudio'
    # Post-processor audio quality
    POST_PROCESSOR_QUALITY = '192'
    # Preferred audio quality name
    PREFERRED_AUDIO_QUALITY = 'bestaudio/best'


class SongExtractorConfig:
    # A list of supported sources by the package
    SUPPORTED_SOURCES = ['youtube']
    # Where to save audio files to
    DESTINATION_FILEPATH = '/Documents/audio-clips/'
