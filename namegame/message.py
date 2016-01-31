class Message(object):
    """
    A message passed between server and client.
    """

    def __init__(self, data=None):
        self.data = data

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__,
                           str(self.data))


class ClientInLobby(Message):
    """
    Message a connected client sends when they login to the server and are ready
    to be picked for a session.
    """


class ClientJoinSession(Message):
    """
    Message that a connected client sends when they want to join a session.
    """


class ClientAcceptInvitation(Message):
    """
    Message that a connected client sends when they accept an invitation to join
    a session.
    """


class ClientRejectInvitation(Message):
    """
    Message that a connected client sends when they reject an invitation to join
    a session.
    """


class ClientInviteClient(Message):
    """
    Message that a connected client sends when they are inviting another to join a
    session.
    """


class ServerInviteClient(Message):
    """
    Message that the server sends a connected client to incite them to join a session.
    """
