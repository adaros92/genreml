import hashlib
import os
import random
import string

from genreml.model.processing import audio
from genreml.model.utils import file_handling


def get_unique_image_name(idx: int) -> str:
    hasher = hashlib.new('md5')
    image_name = "{0}img_{1}_{2}".format(idx, os.getpid(), random.randint(1, 100000))
    random_salt = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(15))
    hasher.update("{0}{1}".format(image_name, random_salt).encode('utf-8'))
    return hasher.hexdigest()


def process_audio_file(root_directory, location: str) -> tuple:
    """ Given a location of an uploaded file, this will run feature extraction and return a tuple containing lists
    of features + images to be displayed to the user
    :param root_directory - the root directory the app is running from
    :param location - the location of a file to extract audio features from
    :returns tuple containing the lists of features extracted
    """
    # Visual features will crash Flask app if the following is not configured
    import matplotlib
    matplotlib.use('Agg')
    # Run feature extraction
    audio_files = audio.AudioFiles()
    audio_format = file_handling.get_filetype(location).replace(".", "")
    audio_files.extract_features(location, cmap=None, figure_height=3, figure_width=5, audio_format=audio_format)
    directory = os.path.join(root_directory, "static")
    visual_feature_paths = []
    for idx, visual_feature in enumerate(audio_files.visual_features[0]):
        # Create unique name for each file generated from visual features
        image_name = get_unique_image_name(idx)
        full_path = "{0}/{1}.png".format(directory, image_name)
        # Save each image
        visual_feature.savefig(full_path)
        visual_feature_paths.append(full_path)
    return audio_files.features, visual_feature_paths
