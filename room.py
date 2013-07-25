# room.py

from .event import Event
from .echo import EchoMixin
from .item import Item


class AbstractRoom(EchoMixin):
    """
    base class for Room
    """

    def __init__(self, name, items=[]):
        super(AbstractRoom, self).__init__()

        self.name = name
        self._items = []
        self.add_items =[]

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
    can contain items
    """

    def __init__(self, name, items=[]):
        super(Room, self).__init__(name, items)

        # EVENTS
        # player entered room
        self.on_enter = Event()
        # player exited room
        self.on_exit = Event()

    def enter(self):
        """
        player has entered the room
        """
        self.on_enter.trigger()

    def exit(self):
        """
        player has left the room
        """
        self.on_exit.trigger()


