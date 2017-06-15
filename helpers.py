import itertools
import linecache
import requests


# Set the maximum number of retries per request before giving up on the request
_MAX_RETRIES = 4

# Set the sleep time between retries
_RETRY_SLEEP = 1

# Set the maximum number of requests before waiting for a period of time
_MAX_NUM_REQUESTS = 20000

# Set the wait time in seconds
_WAIT_TIME = 900

# Set the number of remaining requests before the program should wait
_REMAINING_REQUESTS = _MAX_NUM_REQUESTS

# Set the request success code variable
_REQUEST_SUCCESS = 200

# Set the proxy variables
_PROXIES = {
    'https': ''
}


def perform_request(url):
    """
    Function for performing requests. It handles retries and waiting
    if the maximum number of requests has been reached.

    :param url: string containing the url where the request is targeted
    :return: String containing the source of a web page
    """

    global _REMAINING_REQUESTS, _PROXIES

    # Build a generator for the lazy changing of the proxy
    proxy_list = open('proxy_list.txt')
    proxy_generator = (proxy for proxy in itertools.cycle(proxy_list))
    proxy = eval(proxy_generator.__next__())
    _PROXIES['https'] = proxy['string']

    # Local request function handles retries
    def _request(url):
        global _REMAINING_REQUESTS
        retry_no = 0
        while retry_no < _MAX_RETRIES:
            response = requests.get(url, _PROXIES)
            if response.status_code == _REQUEST_SUCCESS:
                _REMAINING_REQUESTS -= 1
                return response.text
            else:
                retry_no += 1
                _REMAINING_REQUESTS -= 1
                time.sleep(_RETRY_SLEEP)
        return 0

    if _REMAINING_REQUESTS:
        return _request(url)
    else:
        _REMAINING_REQUESTS = _MAX_NUM_REQUESTS
        _PROXIES['https'] = proxy_generator.__next__()['string']
        time.sleep(_WAIT_TIME)
        return _request(url)
