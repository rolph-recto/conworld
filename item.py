# item.py
# objects that reside in a room

from .event import Event
from .echo import EchoMixin


class AbstractItem(EchoMixin):
    """
    base class for item
    doesn't contain any properties or event hooks

    CRITERIA FOR PROPERTIES
    -intrinsic to the item; they are NOT relative to player
        -ex., a room does not have the property "entered" because
        it is relative to the player
    -immutable; cannot change within the course of the game
        -ex., a container does not have the property "opened" (it is a state)

    If it's not a property, it's an object attribute, so declare it as such
    in the constructor
    """

    def __init__(self, name, synonyms=(), description="", properties={}):
        super(AbstractItem, self).__init__()

        # this must be unique to the room
        self._name = name
        self.description = description
        # other names that the item can be called
        # these must also be unique to the room
        self.synonyms = synonyms
        # set of ontological properties of the item
        # ex. liquid, breakable, holdable, takeable, etc.
        self.properties = {}
        self.properties.update(properties)
        # template strings for printing
        self.text = {}

    # name property is read only
    @property
    def name(self):
        return self._name

    def __unicode__(self):
        return self.name.decode()

    def __str__(self):
        return self.name


class Item(AbstractItem):
    """
    objects that reside within the world
    """

    DEFAULT_PROPERTIES = {
        # item can be kept in player's inventory
        "inventory": False,
        # item can be picked up and be put in a container
        "containable": True,
        # item is a container
        "container": False,
    }

    def __init__(self, name, synonyms=(), description="", pty={}):
        super(Item, self).__init__(name, synonyms, description,
            self.__class__.DEFAULT_PROPERTIES)
        print name, pty
        self.properties.update(pty)
        self.container = None # the container the item is in
        self._room = None
        self._player = None # the player whose inventory the item is in

        # EVENTS
        # player looked at this item
        self.on_look = Event()

    @property
    def room(self):
        return self._room

    @room.setter
    def room(self, new_room):
        """
        set the room the item is in
        """
        # unsubscribe current room
        if not self._room == None:
            self.on_echo.unsubscribe(self._room.object_echo)

        # subscribe new room
        self._room = new_room
        # only if it's actually a room, though
        if not new_room == None:
            self.on_echo.subscribe(self._room.object_echo)

    @property
    def player(self):
        return self._player

    @room.setter
    def player(self, new_player):
        """
        set player who possesses the item
        """
        # unsubscribe current player
        if not self._player == None:
            self.on_echo.unsubscribe(self._player.object_echo)

        # subscribe new player
        self._player = new_player
        # only if it's actually a player, though
        if not new_player == None:
            self.on_echo.subscribe(self._player.object_echo)

    def look(self):
        """
        player looked at item
        """
        # print description
        self.echo(self.description)
        self.on_look.trigger()


class Container(Item):
    """
    items that contain other items
    """

    DEFAULT_PROPERTIES = {
        "inventory": False,
        "containable": False,
        "container": True
    }
    TEXT = {
        "OPENED": "The {name} is open.",
        "CLOSED": "The {name} is closed.",
        "LOOK_ITEMS": "The {name} has these items inside it: {items}",
        "LOOK_EMPTY": "The {name} is open but it has nothing inside it.",
        "OPEN": "You open the {name}.",
        "ALREADY_OPEN": "The {name} is already open.",
        "OPEN_LOCKED": "The {name} is locked.",
        "CLOSE": "You close the {name}.",
        "ALREADY_CLOSED": "The {name} is already closed.",
        "UNLOCK": "You unlock the {name}.",
        "ALREADY_UNLOCKED": "The {name} is already unlocked.",
        "ADD": "You put the {item} in the {name}.",
        "ADD_LOCKED": ("You can't put the {item} in the {name} "
            "because it is locked."),
        "ADD_CONTAINED": "The {item} is already in the {container}.",
        "ADD_NOT_CONTAINABLE": "The {item} can't be put in the {name}.",
        "ALREADY_ADDED": "The {item} is already in the {name}.",
        "REMOVE": "You remove the {item} from the {name}.",
        "REMOVE_LOCKED": ("You can't remove the {item} from the {name}"
            "because it is locked."),
        "ALREADY_REMOVED": "The {item} is not in the {name}."
    }

    def __init__(self, name, synonyms=(), description="", properties={},
        opened=False, locked=False):
        super(Container, self).__init__(name, synonyms, description, properties)

        # template strings for printing
        self.text.update(Container.TEXT)
        self._items = []
        self._locked = locked
        self._opened = False if locked else opened

        # EVENTS
        # player opened this container
        self.on_open = Event()
        # player closed this container
        self.on_close = Event()
        # player unlocked the container
        self.on_unlock = Event()
        # player added an item to the container
        self.on_add_item = Event()
        # player remove an item from the container
        self.on_remove_item = Event()

    # opened is read-only
    @property
    def opened(self):
        return self._opened

    # locked is read-only
    @property
    def locked(self):
        return self._locked

    # override Item.room property
    @property
    def room(self):
        return self._room

    @room.setter
    def room(self, new_room):
        """
        set the room the item is in
        """
        # unsubscribe current room
        if not self._room == None:
            self.on_echo.unsubscribe(self._room.object_echo)

        # subscribe new room
        self._room = new_room
        # only if it's actually a room, though
        if not new_room == None:
            self.on_echo.subscribe(self._room.object_echo)

        # set new room for all items in the container as well
        for item in self._items:
            item.room = new_room

    def look(self, describe_self=True, describe_items=True):
        """
        override Item.look() to include items inside the container if it is open
        """
        # print description
        if describe_self:
            self.echo(self.description)
            if self._opened:
                self.echo(self.text["OPENED"].format(name=self.name))
            else:
                self.echo(self.text["CLOSED"].format(name=self.name))

        # print items in the container if it is open
        if describe_items and self._opened:
            opened_str = ""
            items_str = ""

            # multiple items in container
            if len(self._items) > 1:
                opened_str = self.text["LOOK_ITEMS"]

                for item in self._items[:-2]:
                    items_str += "{}, ".format(item.name)

                items_str += "{} ".format(self._items[-2].name)
                items_str += "and {}".format(self._items[-1].name)
            # one item
            elif len(self._items) == 1:
                opened_str = self.text["LOOK_ITEMS"]
                items_str += self._items[0].name
            # no items
            else:
                opened_str = self.text["LOOK_EMPTY"]

            self.echo(opened_str.format(name=self.name, items=items_str))

        # send trigger
        self.on_look.trigger()

    def open(self):
        """
        player opened the container
        """
        if not self._opened:
            if not self._locked:
                self._opened = True
                self.echo(self.text["OPEN"].format(name=self.name))
                # you look inside the container when you open it
                # don't describe the container again, though
                self.look(describe_self=False)
                self.on_open.trigger()
            else:
                self.echo(self.text["OPEN_LOCKED"].format(name=self.name))
        else:
            self.echo(self.text["ALREADY_OPEN"].format(name=self.name))

    def close(self):
        """
        player closed the container
        """
        if self._opened:
            self._opened = False
            self.echo(self.text["CLOSE"].format(name=self.name))
            self.on_close.trigger()
        else:
            self.echo(self.text["ALREADY_CLOSED"].format(name=self.name))

    def unlock(self):
        """
        player unlocks the container
        """
        if self._locked:
            self._locked = False
            self.echo(self.text["UNLOCK"].format(name=self.name))
            self.on_unlock.trigger()
            # open the container too
            self.open()
        else:
            self.echo(self.text["ALREADY_UNLOCKED"].format(name=self.name))

    def add(self, item):
        """
        add item to container
        """
        if not item.container == None:
            self.echo(self.text["ADD_CONTAINED"].format(item=item.name,
                container=item.container.name))
            return

        if item in self._items:
            self.echo(self.text["ALREADY_ADDED"].format(name=self.name,
                item=item.name))
            return

        if not item.properties["containable"]:
            self.echo(self.text["ADD_NOT_CONTAINABLE"].format(name=self.name,
                item=item.name))
            return

        if self._locked:
            self.echo(self.text["ADD_LOCKED"].format(name=self.name,
                item=item.name))
            return
        
        if not self._opened:
            self.echo(self.text["CLOSED"].format(name=self.name))
            return


        item.container = self
        self._items.append(item)
        self.echo(self.text["ADD"].format(name=self.name,
            item=item.name))
        self.on_add_item.trigger()

    def remove(self, item):
        """
        remove item from container
        """
        if not item in self._items:
            self.echo(self.text["ALREADY_REMOVED"].format(name=self.name,
                item=item.name))
            return

        if self._locked:
            self.echo(self.text["REMOVE_LOCKED"].format(name=self.name,
                item=item.name))
            return

        if not self._opened:
            self.echo(self.text["CLOSED"].format(name=self.name))
            return

        item.container = None
        self._items.remove(item)
        self.echo(self.text["REMOVE"].format(name=self.name, item=item.name))
        self.on_remove_item.trigger()

    def get(self, item_name):
        """
        get item by name
        """
        for item in self._items:
            if item.name == item_name:
                return item

        return None

