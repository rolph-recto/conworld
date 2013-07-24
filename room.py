# room.py

from .event import Event
from .echo import EchoMixin
from .item import Item


class Room(EchoMixin):
    """
    atomic constituent of a world (i.e., a set of rooms make a world)
    can contain items
    """

    def __init__(self, name):
        super(Room, self).__init__()
        
        # this must be unique in the scope of the world
        self.name = name

        # EVENTS
        # player entered room
        self.on_enter = Event()
        # player exited room
        self.on_exit = Event()
