# install_twisted_rector must be called before importing  and using the reactor
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout

from namegame.config import install_twisted_reactor

install_twisted_reactor()
from kivy.logger import Logger
from kivy.properties import ObjectProperty

from namegame.config import server_protocol as config
from namegame.message import Message, decode_message, default

from twisted.internet.protocol import connectionDone
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.protocols.basic import LineReceiver

import msgpack
from bidict import bidict


class Server(LineReceiver):
    def __init__(self, factory, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)
        self.factory = factory
        self.setLineMode()

    def connectionMade(self):
        self.factory.on_connection_made(self)

    def connectionLost(self, reason=connectionDone):
        self.factory.on_connection_closed(self, reason)

    def lineReceived(self, data):
        data = msgpack.unpackb(data, ext_hook=decode_message)
        assert isinstance(data, Message)
        response = self.factory.app.handle_message(data, self)
        if response:
            self.sendLine(msgpack.packb(response, default=default))


class Factory(protocol.ServerFactory):
    protocol = Server
    # client_id <-> connection mapping
    clients = bidict()
    connect_callbacks = []
    disconnect_callbacks = []

    def __init__(self, app):
        self.app = app

    def addConnectCallback(self, callable):
        self.connect_callbacks.append(callable)

    def addDisconnectCallback(self, callable):
        self.disconnect_callbacks.append(callable)

    def on_connection_made(self, connection):
        self.clients.inv[connection] = None
        for callback in self.connect_callbacks:
            callback(connection)

    def on_connection_closed(self, connection, reason):
        for callback in self.disconnect_callbacks:
            callback(connection, reason)
        del self.clients.inv[connection]

    def buildProtocol(self, addr):
        return Server(self)


class ServerWidget(FloatLayout):
    '''
        This is the class representing your root widget.
        By default it is inherited from BoxLayout,
        you can use any other layout/widget depending on your usage.
    '''

    cont1 = ObjectProperty(None)
    cont2 = ObjectProperty(None)
    action_bar = ObjectProperty(None)
    manager = ObjectProperty(None)
    status = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_client_connect(self, connection):
        self.set_status("New connection: {}".format(connection))

    def on_client_disconnect(self, connection, reason):
        self.set_status("{} disonnected. Why: {}".format(connection, reason))

    def set_status(self, msg):
        self.status.text = msg

    def handle_message(self, msg, protocol):
        Logger.info("Received: {}".format(msg))
        self.set_status("received:  %s\n" % msg)
        return msg


class GossipServerApp(App):
    factory = None

    def build(self):
        self.factory = Factory(self)
        root = ServerWidget()
        self.factory.addConnectCallback(root.on_client_connect)
        self.factory.addDisconnectCallback(root.on_client_disconnect)
        reactor.listenTCP(config.SERVER_PORT, self.factory)
        return root

    def handle_message(self, msg, protocol):
        return self.root.handle_message(msg, protocol)


if __name__ == '__main__':
    GossipServerApp().run()