
from genreml.model.acquisition import youtube
from genreml.model.utils import file_handling


def download_link(youtube_url: str, directory_path: str, audio_format: str = "wav") -> str:
    """ Downloads a track from the given youtube_url into the given directory_path

    :param youtube_url - the URL to a youtube video containing the audio file to download
    :param directory_path - the path to a local directory in which to save the downloaded file
    :param audio_format - the format of the audio to download
    :returns the full path where the audio was saved to
    """
    assert audio_format in {"wav", "mp3"}
    downloader = youtube.YouTubeDownloader()
    unique_video_id = file_handling.get_unique_file_name(youtube_url)
    full_path = "{0}/{1}.{2}".format(directory_path, unique_video_id, audio_format)
    downloader.download(full_path, url=youtube_url)
    return full_path
