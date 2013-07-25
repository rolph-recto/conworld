# room.py
# a space with a collection of items

from . import DIRECTIONS
from .event import Event
from .echo import EchoMixin
from .item import Item


class Path(object):
    """
    path from one room to another
    """

    def __init__(self, destination, locked=False):
        self.destination = destination
        self.locked = locked


class AbstractRoom(EchoMixin):
    """
    base class for Room
    """

    def __init__(self, name, description="", items=[]):
        super(AbstractRoom, self).__init__()

        self._name = name
        self.description = description
        self._items = []
        self.add_items(items)

    # name property is read-only
    @property
    def name(self):
        return self._name

    def __unicode__(self):
        return self.name.decode()

    def __str__(self):
        return self.name

    def add_item(self, item):
        """
        add a single item to the room
        """
        self.add_items([item])

    def add_items(self, items):
        """
        add a list of items to the room
        """
        for item in items:
            if not item in self._items:
                item.room = self
                self._items.append(item)
            else:
                raise RuntimeError("{item} is already in {room}"
                    .format(item=item.name, room=self.name))

    def remove_item(self, item):
        """
        remove an item from the room
        """
        if item in self._items:
            item.room = None
            self._items.remove(item)
        else:
            raise RuntimeError("{item} is not in {room}"
                .format(item=item.name, room=self.name))

    def object_echo(self, msg):
        """
        relay object echo messages up to the echo listeners of the room
        (one of which will be the IO driver)
        """
        self.echo(msg)


class Room(AbstractRoom):
    """
    atomic constituent of a world (i.e., a set of rooms make a world)
    can contain items and paths to other rooms
    """

    def __init__(self, name, items=[], world=None):
        super(Room, self).__init__(name, items)
        # paths to other rooms
        self._path = dict[(direction, None) for direction in DIRECTIONS]
        self._world = None
        self.world = world

        # EVENTS
        # player entered room
        self.on_enter = Event()
        # player exited room
        self.on_exit = Event()
        # player looks around room
        self.on_look() = Event()

    @property
    def world(self):
        return self._world

    @world.setter
    def world(self, new_world):
        """
        set the world the room is in
        """
        # unsubscribe current world
        if not self._world == None:
            self.on_echo.unsubscribe(self._world.room_echo)

        # subscribe new world
        self._world = new_world
        # only if it's actually a world, though
        if not new_world == None:
            self.on_echo.subscribe(self._world.room_echo)

    def enter(self):
        """
        player has entered the room
        """
        self.echo(self.description)
        self.on_enter.trigger()

    def exit(self):
        """
        player has left the room
        """
        self.on_exit.trigger()


