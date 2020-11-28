from genreml.model.utils import multithreading


class MockReceiver(object):

    def __init__(self):
        self.records = []
        self.random_strings = []

    def insert(self, records: list, some_random_string: str):
        self.records += records
        self.random_strings += [some_random_string for _ in records]


def test_run_function_in_threads():
    """ Tests utils.multithreading.run_function_in_threads function """
    receiver = MockReceiver()
    data = [x for x in range(18)]
    length_of_data = len(data)
    original_data = data.copy()
    number_of_threads = 10
    multithreading.run_function_in_thread(number_of_threads, receiver.insert, data, "some_random_string")
    assert len(receiver.records) == length_of_data and len(receiver.random_strings) == length_of_data
    assert receiver.records == original_data \
           and receiver.random_strings == ["some_random_string" for _ in range(length_of_data)]
