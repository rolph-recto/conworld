# echo.py
# echo mixin

from .event import Event


class EchoMixin(object):
    """
    Adds functionality to print to IO driver
    """

    def __init__(self):
        self.on_echo = Event()

        # call the next mixin constructor, if it exists
        # this makes multiple inheritance work
        super(EchoMixin, self).__init__()

    def echo(self, msg):
        """
        send off to subscribers (the last of which should be the IO Driver)
        """
        self.on_echo.trigger(msg)
