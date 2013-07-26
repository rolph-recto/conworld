# room.py
# a space with a collection of items

from . import DIRECTIONS, enumerate_items
from .event import Event
from .echo import EchoMixin
from .item import Item


class Path(object):
    """
    path from one room to another
    """

    def __init__(self, destination, blocked=False):
        self.destination = destination
        self.blocked = blocked


class AbstractRoom(EchoMixin):
    """
    base class for Room
    """

    def __init__(self, name, description="", items=[]):
        super(AbstractRoom, self).__init__()

        self._name = name
        self.description = description
        self._items = []
        self.add(items)

    # name property is read-only
    @property
    def name(self):
        return self._name

    def __unicode__(self):
        return self.name.decode()

    def __str__(self):
        return self.name

    def add(self, items):
        """
        add a list of items to the room
        """
        if not type(items) == list:
            items = [items]

        for item in items:
            if not item in self._items:
                item.room = self
                self._items.append(item)

                #if the item was in the player's inventory, take it off
                item.player = None

                # add items in a container
                if item.container:
                    for con_item in item.items:
                        self.add(con_item)

    def remove(self, item):
        """
        remove an item from the room
        """
        if item in self._items:
            item.room = None
            self._items.remove(item)

            # remove items in a container
            if item.container:
                for con_item in item.items:
                    self.remove(con_item)

        else:
            raise RuntimeError("{item} is not in {room}"
                .format(item=item.name, room=self.name))

    def get(self, item_name):
        """
        get item by name
        """
        for item in self._items:
            if item.name == item_name or item_name in item.synonyms:
                return item

        return None

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

    TEXT = {
        "ENTER": "You enter the {room}.",
        "LOOK_PATH": "Looking {direction}wards, you see the {destination}. ",
        "LOOK_PATH_BLOCK": ("Looking {direction}wards, you see the "
            "{destination}, but the path is blocked."),
        "LOOK_ITEMS": ("Looking around the {room}, you see the "
            "following items: {items}"),
        "LOOK_EMPTY": "Looking around the {room}, you don't see any items.",
    }

    def __init__(self, name, description="", items=[], world=None):
        super(Room, self).__init__(name, description, items)
        # paths to other rooms
        self._paths = dict([(direction, None) for direction in DIRECTIONS])
        self._world = None
        self.world = world
        self.text = {}
        self.text.update(Room.TEXT)

        # EVENTS
        # player entered room
        self.on_enter = Event()
        # player exited room
        self.on_exit = Event()
        # player looks around room
        self.on_look = Event()

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
        # player looks around when he/she enters
        self.echo(self.text["ENTER"].format(room=self.name))
        self.look()
        self.on_enter.trigger()

    def exit(self):
        """
        player has left the room
        """
        self.on_exit.trigger()

    def look(self):
        """
        player looks around the room
        """
        self.echo(self.description)

        # describe paths
        look_path = ""
        for direction, path in self._paths.iteritems():
            if not path == None:
                if not path.blocked:
                    look_path += self.text["LOOK_PATH"].format(
                        direction=direction, destination=path.destination)
                else:
                    look_path += self.text["LOOK_PATH_BLOCKED"].format(
                        direction=direction, destination=path.destination)

        self.echo(look_path)

        # describe items
        look_str = ""
        # can't see items in closed containers
        visible_items = [item for item in self._items if item.owner == None]

        # multiple items in container
        if len(visible_items) >= 1:
            look_str = self.text["LOOK_ITEMS"]
        # no items
        else:
            look_str = self.text["LOOK_EMPTY"]

        items_str = enumerate_items([item.name for item in visible_items])

        self.echo(look_str.format(room=self.name, items=items_str))

        self.on_look.trigger()

    def add_path(self, direction, destination, blocked=False):
        """
        add a path to another room
        """
        if direction in DIRECTIONS:
            path = Path(destination, blocked)
            self._paths[direction] = path
        else:
            raise ValueError("{} is not a direction".format(direction))

    def remove_path(self, dir_dest):
        """
        remove a path by direction or by destination
        """
        # by direction
        if type(dir_dest) == str:
            if dir_dest in DIRECTION:
                self._paths[dir_dest] = None
            else:
                raise ValueError("{} is not a direction".format(dir_dest))

        # by destination
        elif type(dir_dest) == Room:
            rm_dir = ""
            for direction, destination in self._paths.iteritems():
                if dir_dest == destination:
                    rm_dir = direction
                    break

            # we found the destination; remove its path
            if not rm_dir == "":
                self._paths[rm_dir] = None

    def get_path(self, direction):
        if direction in DIRECTIONS:
            return self._paths[direction]
        else:
            raise ValueError("{} is not a direction".format(dir_dest))



