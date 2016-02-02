from kivy.support import install_twisted_reactor

install_twisted_reactor()

from namegame.server import Factory as ServerFactory
from namegame.client import Factory as ClientFactory
from twisted.trial.unittest import TestCase
from twisted.test import proto_helpers
from twisted.python import log
import sys

log.startLogging(sys.stdout)

from twisted.internet.defer import Deferred, maybeDeferred, \
    gatherResults
from unittest import mock
from ..config import DotDict, server_protocol, client_protocol

letters = list("qwertyuioplkjhasdfgzxcvbnm")


class TestDotDict(TestCase):
    def setUp(self):
        self.dict = DotDict({letter: number for number, letter in enumerate(letters)})

    def tearDown(self):
        del self.dict

    def test_dot_read(self):
        assert self.dict['a'] == self.dict.a

    def test_dot_write(self):
        self.dict.a = 'pass'
        assert self.dict['a'] == 'pass'

    def test_key_restriction(self):
        def integer_key():
            self.dict['0'] = 0

        self.assertRaises(Exception, integer_key)


class TestBasicConnection(TestCase):
    timeout = 10

    def setUp(self):
        deferred1, deferred2 = [Deferred() for _ in range(2)]

        self.server_app = mock.MagicMock()
        self.server_deferred = Deferred()
        self.server_factory = ServerFactory(self.server_app)
        self.server_transport = proto_helpers.StringTransport()
        self.server_connection = self.server_factory.buildProtocol(server_protocol.SERVER_PORT)
        self.server_factory.onConnectionLost = self.server_deferred
        self.server_factory.onConnectionMade = deferred1

        self.client_app = mock.MagicMock()
        self.client_deferred = Deferred()
        self.client_factory = ClientFactory(self.client_app)
        self.client_connection = self.client_factory.buildProtocol((client_protocol.SERVER_IP,
                                                                    client_protocol.SERVER_PORT))
        self.client_transport = proto_helpers.StringTransport()
        self.client_factory.onConnectionLost = self.client_deferred
        self.client_factory.onConnectionMade = deferred2

        def on_server_connect(*args):
            log.msg("Server transport disconnected.")

        deferred1.addCallback(on_server_connect)

        def on_client_connect(*args):
            log.msg("Client transport connected.")

        deferred2.addCallback(on_client_connect)

        deferred_last = Deferred()

        def on_connect(connection):
            self.client = connection
            deferred_last.callback(True)
            log.msg("Client connected")

        self.client_app.on_connection = on_connect

        self.client_connection.makeConnection(self.client_transport)
        return gatherResults([deferred2, deferred1, deferred_last])

    def tearDown(self):
        d = maybeDeferred(self.server_connection.stopListening)
        self.client_connection.disconnect()
        self.client.abortConnection()
        d = gatherResults([self.client_deferred,
                           self.server_deferred,
                           d])
        log.msg("Returning " + str(d))
        from sys import stdout
        stdout.flush()
        return d

        # def test_handle_message(self):
        #     log.msg("Testing...")
        #     self.client.write(encode(Message('test')))
        #     log.msg("Tested")
