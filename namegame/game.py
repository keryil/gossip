class Player(object):
    def __init__(self, id, connection):
        self.id = id
        self.connection = connection


class Round(object):
    """
    Represents a round in a session.
    """

    def __init__(self):
        self.hearer = None
        self.speaker = None
        self.target = None
        self.guess = None
        self.success = None


class Session(object):
    """
    Represents a game session.
    """

    def __init__(self, meanings, nplayers=2):
        self.players = [None for _ in range(nplayers)]
        self.started = False
        self.rounds = []
        self.meanings = meanings
