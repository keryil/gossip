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


_twisted_reactor_stopper = None
_twisted_reactor_work = None


def _install_twisted_reactor(**kwargs):
    '''Installs a threaded twisted reactor, which will schedule one
    reactor iteration before the next frame only when twisted needs
    to do some work.

    Any arguments or keyword arguments passed to this function will be
    passed on the the threadedselect reactors interleave function. These
    are the arguments one would usually pass to twisted's reactor.startRunning.

    Unlike the default twisted reactor, the installed reactor will not handle
    any signals unless you set the 'installSignalHandlers' keyword argument
    to 1 explicitly. This is done to allow kivy to handle the signals as
    usual unless you specifically want the twisted reactor to handle the
    signals (e.g. SIGINT).

    .. note::
        Twisted is not included in iOS build by default. To use it on iOS,
        put the twisted distribution (and zope.interface dependency) in your
        application directory.
    '''

    # prevent installing more than once
    if '_kivy_twisted_reactor_installed' in globals():
        return
    global _kivy_twisted_reactor_installed
    _kivy_twisted_reactor_installed = True

    # don't let twisted handle signals, unless specifically requested
    kwargs.setdefault('installSignalHandlers', 0)

    # install threaded-select reactor, to use with own event loop
    kwargs['_threadedselect'].install()
    del kwargs['_threadedselect']

    # now we can import twisted reactor as usual
    from twisted.internet import reactor
    from twisted.internet.error import ReactorNotRunning

    from collections import deque
    from kivy.base import EventLoop
    from kivy.logger import Logger
    from kivy.clock import Clock

    # will hold callbacks to twisted callbacks
    q = deque()

    # twisted will call the wake function when it needs to do work
    def reactor_wake(twisted_loop_next):
        '''Wakeup the twisted reactor to start processing the task queue
        '''

        Logger.trace("Support: twisted wakeup call to schedule task")
        q.append(twisted_loop_next)

    # called every frame, to process the reactors work in main thread
    def reactor_work(*args):
        '''Process the twisted reactor task queue
        '''
        Logger.trace("Support: processing twisted task queue")
        while len(q):
            q.popleft()()

    global _twisted_reactor_work
    _twisted_reactor_work = reactor_work

    # start the reactor, by telling twisted how to wake, and process
    def reactor_start(*args):
        '''Start the twisted reactor main loop
        '''
        Logger.info("Support: Starting twisted reactor")
        reactor.interleave(reactor_wake, **kwargs)
        Clock.schedule_interval(reactor_work, 0)

    # make sure twisted reactor is shutdown if eventloop exists
    def reactor_stop(*args):
        '''Shutdown the twisted reactor main loop
        '''
        if reactor.threadpool:
            Logger.info("Support: Stopping twisted threads")
            reactor.threadpool.stop()
        Logger.info("Support: Shutting down twisted reactor")
        reactor._mainLoopShutdown()
        try:
            reactor.stop()
        except ReactorNotRunning:
            pass

        import sys
        sys.modules.pop('twisted.internet.reactor', None)

    global _twisted_reactor_stopper
    _twisted_reactor_stopper = reactor_stop

    # start and stop the reactor along with kivy EventLoop
    Clock.schedule_once(reactor_start, 0)
    EventLoop.bind(on_stop=reactor_stop)


def uninstall_twisted_reactor():
    '''Uninstalls the Kivy's threaded Twisted Reactor. No more Twisted
    tasks will run after this got called. Use this to clean the
    `twisted.internet.reactor` .

    .. versionadded:: 1.9.0
    '''

    # prevent uninstalling more than once
    if not '_kivy_twisted_reactor_installed' in globals():
        return
    global _kivy_twisted_reactor_installed

    from kivy.base import EventLoop

    global _twisted_reactor_stopper
    _twisted_reactor_stopper()
    EventLoop.unbind(on_stop=_twisted_reactor_stopper)

    del _kivy_twisted_reactor_installed


def install_twisted_reactor():
    import _threadedselect

    _install_twisted_reactor(_threadedselect=_threadedselect)

server_protocol = DotDict()
client_protocol = DotDict()

server_protocol.SERVER_PORT = 8989
client_protocol.SERVER_PORT = 8989
client_protocol.SERVER_IP = '127.0.0.1'
client_protocol.DELIMITER = server_protocol.DELIMITER = "\r\n"
