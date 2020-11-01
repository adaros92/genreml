# Name: string_parsing.py
# Description: defines utility functions to parse string objects


def str_to_collection(str_to_parse: str, collection_to_parse_to: any, delim: str = ','):
    """ Converts a given string with the given delimeter into an object of the given type

    :param str_to_parse - the string to parse into an object
    :param collection_to_parse_to - the class of the collection to parse the string to
    :param delim - the delimeter that separates values in the string
    :returns a collection of values parsed from the given string
    """
    if collection_to_parse_to not in (set, dict, list):
        raise RuntimeError(
            "a string cannot be parsed into the given collection of {0}", format(str(collection_to_parse_to)))
    if not str_to_parse:
        str_list = []
    else:
        str_list = str_to_parse.split(delim)
    return collection_to_parse_to(str_list)
