import re

import msgpack


class Message(object):
    """
    A message passed between server and client.
    """
    exttype_code = 0
    data_constructor = str
    def __init__(self, data=None):
        self.data = data

    @classmethod
    def FromString(cls, string):
        matches = re.search("(\w+)\((.+?)\)", string).groups()
        assert matches[0] == cls.__name__.split('.')[-1]
        data = cls.data_constructor(matches[1])
        return cls(data)

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           str(self.data))


class ClientInLobby(Message):
    """
    Message a connected client sends when they login to the server and are ready
    to be picked for a session. Argument data holds client id.
    """
    exttype_code = 1

class ClientJoinSession(Message):
    """
    Message that a connected client sends when they want to join a session.
    """
    exttype_code = 2


class ClientAcceptInvitation(Message):
    """
    Message that a connected client sends when they accept an invitation to join
    a session.
    """
    exttype_code = 3


class ClientRejectInvitation(Message):
    """
    Message that a connected client sends when they reject an invitation to join
    a session.
    """
    exttype_code = 4


class ClientInviteClient(Message):
    """
    Message that a connected client sends when they are inviting another to join a
    session.
    """
    exttype_code = 5


class ServerInviteClient(Message):
    """
    Message that the server sends a connected client to incite them to join a session.
    """
    exttype_code = 6


def default(message):
    if isinstance(message, Message):
        return msgpack.ExtType(Message.exttype_code,
                               str(message).encode("utf-8"))


def decode_message(code, obj):
    if code == Message.exttype_code:
        return Message.FromString(obj.decode("utf-8"))
