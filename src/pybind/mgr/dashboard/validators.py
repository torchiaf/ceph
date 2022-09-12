from urllib.parse import urlparse


def valid_url(to_validate: str) -> bool:
    """
    Return whether or not given value is a valid URL.
    If the value is valid URL this function returns ``True``

    Examples::

        >>> url_validator('http://foobar.dk')
        True

        >>> url_validator('http://10.0.0.1')
        True

        >>> url_validator('http://foo:bar')
        False

        >>> url_validator('foo://localhost:8080')
        False

    :param to_validate: URL address string to validate
    """

    try:
        v = urlparse(to_validate)
        if (v.scheme in ('http', 'https')
            and v.netloc
            and (
                v.port is None
                or v.port)):
            return True
    except Exception:
        pass

    return False
