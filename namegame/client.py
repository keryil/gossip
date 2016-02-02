#install_twisted_rector must be called before importing the reactor
from namegame.config import install_twisted_reactor

install_twisted_reactor()

from kivy.logger import Logger
from twisted.internet import reactor, protocol
from twisted.protocols.basic import LineReceiver
# from jsonpickle import encode, decode
from namegame.config import client_protocol as settings

from namegame.message import Message, default, decode_message, \
    ClientInLobby
import msgpack


class Client(LineReceiver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLineMode()
        # self.delimiter = settings.DELIMITER
        self.connect_callbacks = []
        self.disconnect_callbacks = []

    def addConnectCallback(self, callable):
        self.connect_callbacks.append(callable)

    def addDisconnectCallback(self, callable):
        self.disconnect_callbacks(callable)

    def connectionMade(self):
        self.factory.app.on_connection(self.transport)

    def lineReceived(self, data):
        data = msgpack.unpackb(data, ext_hook=decode_message)
        assert isinstance(data, Message)
        print(data)
        self.factory.app.print_message(data)


class Factory(protocol.ClientFactory):
    protocol = Client

    def __init__(self, app):
        self.app = app

    def clientConnectionLost(self, conn, reason):
        self.app.print_message("connection lost")

    def clientConnectionFailed(self, conn, reason):
        self.app.print_message("connection failed")


from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


# A simple kivy App, with a textbox to enter messages, and
# a large label to display all the messages received from
# the server
class TwistedClientApp(App):
    client = None

    def build(self):
        root = self.setup_gui()
        self.connect_to_server()
        return root

    def setup_gui(self):
        self.readybtn = Button(text="Enter lobby")
        self.readybtn.bind(on_press=self.enter_lobby)
        self.textbox = TextInput(size_hint_y=.1, multiline=False)
        self.textbox.bind(on_text_validate=self.send_message)
        self.label = Label(text='connecting...\n')
        self.layout = BoxLayout(orientation='vertical')
        self.layout.add_widget(self.label)
        self.layout.add_widget(self.textbox)
        self.layout.add_widget(self.readybtn)
        return self.layout

    def enter_lobby(self, btn):
        msg = ClientInLobby()
        self.send_to_server(msg)

    def connect_to_server(self):
        reactor.connectTCP(settings.SERVER_IP,
                           settings.SERVER_PORT,
                           Factory(self))

    def on_connection(self, connection):
        self.print_message("connected succesfully!")
        self.client = connection

    def send_message(self, textbox):
        msg = Message(str(textbox.text))
        self.send_to_server(msg)

    def send_to_server(self, message):
        assert isinstance(message, Message)
        assert self.client
        Logger.info("Encode and send to server: {}".format(message))
        self.client.protocol.sendLine(msgpack.packb(message, default=default))
        self.textbox.text = ""

    def print_message(self, msg):
        self.label.text += str(msg) + "\n"

if __name__ == '__main__':
    TwistedClientApp().run()