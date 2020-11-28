from threading import Thread


def run_function_in_thread(number_of_threads: int, function_to_run, data: list, *args):
    """ Given a number of parallel threads, a function to run, some data to provide the function, and any other
    arguments the functin requires, this will run the function in separate theads

    :param number_of_threads - how many threads to create
    :param function_to_run - the function to run in those threads
    :param data - the data to run the function with (will be split evenly across the threads)
    :param args - other positional arguments required by the fucntion if any
    """
    data_length = len(data)
    assert number_of_threads > 0 and data_length > 0
    threads = [Thread()] * number_of_threads
    # Each thread will process this much of the data
    number_of_data_slices = round(data_length / number_of_threads)
    thread_count = 0
    # Chunk up the data by number of slices to process in each thread and kick off the threads
    data_chunks = [data[idx:idx+number_of_data_slices] for idx in range(0, data_length, number_of_data_slices)]
    data_chunks_length = len(data_chunks)
    for thread in range(number_of_threads):
        # If there is no data to process then just skip creation of the thread
        if len(data) == 0 or thread + 1 > data_chunks_length:
            continue
        data_to_run_with = data_chunks[thread]
        threads[thread] = Thread(target=function_to_run, args=(data_to_run_with, *args))
        threads[thread].start()
        thread_count += 1
    # Wait for all the threads to finish
    for thread in range(thread_count):
        threads[thread].join()
