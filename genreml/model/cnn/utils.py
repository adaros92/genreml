import pandas as pd
import pkg_resources


def get_resource_csv(filename: str) -> pd.DataFrame:
    """ Retrieves a CSV file from the model resources packaged up with genreml

    :param filename - the name of the file to retrieve
    :returns a data frame constructed from the CSV file
    """
    if filename[-4:] != ".csv":
        raise ValueError("Filename {0} does not correspond to a CSV".format(filename))
    directory = pkg_resources.resource_filename('genreml', 'model_resources/')
    return pd.read_csv(directory + filename)
