import pytest

from genreml.model.utils import string_parsing


def test_str_to_collection():
    """ Tests genreml.model.utils.string_parsing.str_to_collection function """
    sample_str = 'something,in,a,string'
    # Test nominal operation
    assert string_parsing.str_to_collection(sample_str, set) == {'something', 'in', 'a', 'string'}
    assert string_parsing.str_to_collection(sample_str, list) == ['something', 'in', 'a', 'string']
    # Test wrong delim type
    assert string_parsing.str_to_collection(sample_str, list, delim='\t') == [sample_str]
    # Test unsupported collection type
    with pytest.raises(RuntimeError):
        string_parsing.str_to_collection(sample_str, str)
