# coding=utf-8
"""Client for working with QCS's API.

This module provides a flexible API client for talking with the quipucords
server, allowing the user to customize how return codes are handled depending
on the context.

"""

import requests

from urllib.parse import urljoin, urlunparse

from camayoc import config
from camayoc import exceptions
from camayoc.constants import (
    QCS_API_VERSION,
    QCS_TOKEN_PATH,
)


def echo_handler(response):
    """Immediately return ``response``."""
    return response


def code_handler(response):
    """Check the response status code, and return the response.

    :raises: ``requests.exceptions.HTTPError`` if the response status code is
        in the 4XX or 5XX range.
    """
    response.raise_for_status()
    return response


def json_handler(response):
    """Like ``code_handler``, but also return a JSON-decoded response body.

    Do what :func:`camayoc.api.code_handler` does. In addition, decode the
    response body as JSON and return the result.
    """
    response.raise_for_status()
    return response.json()


class Client(object):
    """A client for interacting with the quipucords API.

    This class is a wrapper around the ``requests.api`` module provided by
    `Requests`_. Each of the functions from that module are exposed as methods
    here, and each of the arguments accepted by Requests' functions are also
    accepted by these methods. The difference between this class and the
    `Requests`_ functions lies in its configurable request and response
    handling mechanisms.

    All requests made via this client use the base URL of the qcs server
    provided in your ``$XDG_CONFIG_HOME/camayoc/config.yaml``.

    You can override this base url by assigning a new value to the url
    field.

    Example::
        >>> from camayoc import api
        >>> client = api.Client()
        >>> # I can now make requests to the QCS server
        >>> # using relative paths, because the base url is
        >>> # was set using my config file.
        >>>
        >>> client.get('/credentials/hosts/')
        >>>
        >>> # now if I want to do something else,
        >>> # I can change the base url
        >>> client.url = 'https://www.whatever.com'

    .. _Requests: http://docs.python-requests.org/en/master/
    """

    def __init__(self, response_handler=None, url=None, authenticate=True):
        """Initialize this object, collecting base URL from config file.

        If no response handler is specified, use the `code_handler` which will
        raise an exception for 'bad' return codes.


        If no URL is specified, then the config file will be parsed and the URL
        will be built by reading the hostname, port and https values. You can
        configure the default URL by including the following on your Camayoc
        configuration file::

            qcs:
                hostname: <machine_hostname_or_ip_address>
                port: <port>  # if not defined will take the default port
                              # depending on the https config: 80 if https is
                              # false and 443 if https is true.
                https: false  # change to true if server is published over
                              # https. Defaults to false if not defined
        """
        self.url = url
        self.token = None

        if not self.url:
            cfg = config.get_config().get('qcs', {})
            hostname = cfg.get('hostname')

            if not hostname:
                raise exceptions.QCSBaseUrlNotFound(
                    "\n'qcs' section specified in camayoc config file, but"
                    "no 'hostname' key found."
                )

            scheme = 'https' if cfg.get('https', False) else 'http'
            port = str(cfg.get('port', ''))
            netloc = hostname + ':{}'.format(port) if port else hostname
            self.url = urlunparse(
                (scheme, netloc, QCS_API_VERSION, '', '', ''))

        if not self.url:
            raise exceptions.QCSBaseUrlNotFound(
                'No base url was specified to the client either with the '
                'url="host" option or with the camayoc config file.')

        if response_handler is None:
            self.response_handler = code_handler
        else:
            self.response_handler = response_handler

        if authenticate:
            self.login()

    def login(self):
        """Login to the server to receive an authorization token."""
        cfg = config.get_config().get('qcs', {})
        server_username = cfg.get('username', 'admin')
        server_password = cfg.get('password', 'pass')
        login_request = self.request(
            'POST',
            urljoin(self.url, QCS_TOKEN_PATH),
            json={
                'username': server_username,
                'password': server_password
            }
        )
        self.token = login_request.json()['token']
        return login_request

    def logout(self):
        """Start sending unauthorized requests.

        There is no API interaction that need occur to logout.
        We simply must send unauthorized requests.
        """
        self.token = None

    def default_headers(self):
        """Build the headers for our request to the server."""
        if self.token:
            return {'Authorization': 'Token {}'.format(self.token)}
        return {}

    def delete(self, endpoint, **kwargs):
        """Send an HTTP DELETE request."""
        url = urljoin(self.url, endpoint)
        return self.request(
            'DELETE',
            url,
            headers=self.default_headers(),
            **kwargs)

    def get(self, endpoint, **kwargs):
        """Send an HTTP GET request."""
        url = urljoin(self.url, endpoint)
        return self.request(
            'GET',
            url,
            headers=self.default_headers(),
            **kwargs)

    def options(self, endpoint, **kwargs):
        """Send an HTTP OPTIONS request."""
        url = urljoin(self.url, endpoint)
        return self.request(
            'OPTIONS',
            url,
            headers=self.default_headers(),
            **kwargs)

    def head(self, endpoint, **kwargs):
        """Send an HTTP HEAD request."""
        url = urljoin(self.url, endpoint)
        return self.request(
            'HEAD',
            url,
            headers=self.default_headers(),
            **kwargs)

    def post(self, endpoint, payload, **kwargs):
        """Send an HTTP POST request."""
        url = urljoin(self.url, endpoint)
        return self.request(
            'POST',
            url,
            headers=self.default_headers(),
            json=payload,
            **kwargs)

    def put(self, endpoint, payload, **kwargs):
        """Send an HTTP PUT request."""
        url = urljoin(self.url, endpoint)
        return self.request(
            'PUT',
            url,
            headers=self.default_headers(),
            json=payload,
            **kwargs)

    def request(self, method, url, **kwargs):
        """Send an HTTP request.

        Arguments passed directly in to this method override (but do not
        overwrite!) arguments specified in ``self.request_kwargs``.
        """
        # The `self.request_kwargs` dict should *always* have a "url" argument.
        # This is enforced by `self.__init__`. This allows us to call the
        # `requests.request` function and satisfy its signature:
        #
        #     request(method, url, **kwargs)
        #
        return self.response_handler(requests.request(method, url, **kwargs))
