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
        # self.delimiter = config.DELIMITER
        self.connect_callbacks = []
        self.disconnect_callbacks = []

    def addConnectCallback(self, callable):
        self.connect_callbacks.append(callable)

    def addDisconnectCallback(self, callable):
        self.disconnect_callbacks(callable)

    def connectionMade(self):
        self.factory.clients.inv[self] = None
        for callback in self.connect_callbacks:
            callback()

    def connectionLost(self, reason=connectionDone):
        for callback in self.disconnect_callbacks:
            callback(reason)
        del self.factory.clients.inv[self]

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

    def __init__(self, app):
        self.app = app

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.contextualViewSessions = actionbar.ContextualActionView(
        #     action_previous=actionbar.ActionPrevious(title='Sessions'))
        # self.contextualViewClients = actionbar.ContextualActionView(
        #     action_previous=actionbar.ActionPrevious(title='Clients'))

        # def go_home(*args):
        #     self.manager.current = "Main"
        #     Logger.info("Went home.")
        # self.action_bar.bind(on_previous=self.on_previous)
        # self.prev_index = 0
        # self.from_actionbar = False

        # def on_index(self, instance, value):
        #     if value == 2:
        #         # self.action_bar.add_widget(self.contextualView)
        #         pass
        #     elif value == 1:
        #         if self.prev_index == 0:
        #             # self.action_bar.add_widget(self.contextualView)
        #             pass
        #         elif not self.from_actionbar:
        #             try:
        #                 self.action_bar.on_previous()
        #             except:
        #                 pass
        #
        #         # elif self.from_actionbar:
        #         #     self.carousel.index = 0
        #         #     value = 0
        #
        #     elif self.from_actionbar is False:
        #             try:
        #                 self.action_bar.on_previous()
        #             except:
        #                 pass
        #
        #     self.prev_index = value
        #     self.from_actionbar = False
        #
        # def on_previous(self, *args):
        #     self.manager.screent =
        #     # self.from_actionbar = True
        #     # self.sm.index = 0

    def handle_message(self, msg, protocol):
        Logger.info("Received: {}".format(msg))
        self.label.text = "received:  %s\n" % msg
        return msg


class GossipServerApp(App):
    def build(self):
        # self.label = Label(text="server started\n")
        reactor.listenTCP(config.SERVER_PORT, Factory(self))
        return ServerWidget()
        # return self.label

    def handle_message(self, msg, protocol):
        Logger.info("Received: {}".format(msg))
        self.label.text = "received:  %s\n" % msg
        return msg


if __name__ == '__main__':
    GossipServerApp().run()