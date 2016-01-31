import re


class DotDict(dict):
    """
    A dictionary that supports configuration.key type of access.

    Can do regular dict stuff
    >>> d = DotDict()
    >>> d['k'] = 'v'
    >>> d['k']
    'v'

    Can access values via dict.key
    >>> d.k == d['k']
    True

    Assignments also work.
    >>> d.k = 'v2'
    >>> d.k == d['k']
    True

    You cannot use keys that start with numbers because they aren't
    valid attribute names.
    >>> d['2k'] = 'v'
    Traceback (most recent call last):
        ...
    Exception: You cannot use keys that start with integers.
    """

    def __init__(self, *args, **kwargs):
        super(DotDict, self).__init__(*args, **kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return getattr(super(DotDict, self), key)

    def __setattr__(self, key, value):
        try:
            self[key] = value
        except KeyError:
            dict.__setattr__(self, key, value)

    def __setitem__(self, key, value):
        """
        We don't allow keys that start with an integer, because they can't be used
        as attribute names.
        :param key:
        :param value:
        :return:
        """
        found = re.search("^\d+", key)
        if found:
            raise Exception("You cannot use keys that start with integers.")
        else:
            dict.__setitem__(self, key, value)


server_protocol = DotDict()
client_protocol = DotDict()
