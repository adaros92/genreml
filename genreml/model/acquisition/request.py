import requests


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
