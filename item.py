# item.py

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
        self.name = name
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


class Item(AbstractItem):
    """
    objects that reside within the world
    """

    DEFAULT_PROPERTIES = {
        # item can be kept in player's inventory (and thus can be picked up)
        "inventory": False,
        # item is a container
        "container": False
    }

    def __init__(self, name, synonyms=(), description="", properties={}):
        super(Item, self).__init__(name, synonyms, description,
            self.__class__.DEFAULT_PROPERTIES)
        self.properties.update(properties)

        # EVENTS
        # player looked at this item
        self.on_look = Event()

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
        "container": True
    }
    LOOK_OPEN = "{description} It is open."
    LOOK_CLOSED = "{description} It is closed."
    LOOK_ITEMS = "The {name} has these items inside it: {items}"
    LOOK_EMPTY = "The {name} is open but it has nothing inside it."
    OPEN = "You open the {name}."
    ALREADY_OPEN = "The {name} is already open."
    OPEN_LOCKED = "The {name} is locked."
    CLOSE = "You close the {name}."
    ALREADY_CLOSED = "The {name} is already closed."
    UNLOCK = "You unlock the {name}."
    ALREADY_UNLOCKED = "The {name} is already unlocked."

    def __init__(self, name, synonyms=(), description="", properties={},
        opened=False, locked=False):
        super(Container, self).__init__(name, synonyms, description, properties)
        # template strings for printing
        self.text.update({
            "LOOK_OPEN": Container.LOOK_OPEN,
            "LOOK_CLOSED": Container.LOOK_CLOSED,
            "LOOK_ITEMS": Container.LOOK_ITEMS,
            "LOOK_EMPTY": Container.LOOK_EMPTY,
            "OPEN": Container.OPEN,
            "ALREADY_OPEN": Container.ALREADY_OPEN,
            "OPEN_LOCKED": Container.OPEN_LOCKED,
            "CLOSE": Container.CLOSE,
            "ALREADY_CLOSED": Container.ALREADY_CLOSED,
            "UNLOCK": Container.UNLOCK,
            "ALREADY_UNLOCKED": Container.ALREADY_UNLOCKED
        })
        self.items = []
        self._opened = opened
        self._locked = locked

        # EVENTS
        # player opened this container
        self.on_open = Event()
        # player closed this container
        self.on_close = Event()
        # player unlocked the container
        self.on_unlock = Event()

    # opened is read-only
    @property
    def opened(self):
        return self._opened

    # locked is read-only
    @property
    def locked(self):
        return self._locked

    def look(self, describe_self=True, describe_items=True):
        """
        override Item.look() to include items inside the container if it is open
        """
        # print description
        if describe_self:
            if self._opened:
                self.echo(self.text["LOOK_OPEN"]
                    .format(description=self.description))
            else:
                self.echo(self.text["LOOK_CLOSED"]
                    .format(description=self.description))

        # print items in the container if it is open
        if describe_items and self._opened:
            opened_str = ""
            items_str = ""

            # multiple items in container
            if len(self.items) > 1:
                opened_str = self.text["LOOK_ITEMS"]

                for item in self.items[:-1]:
                    items_str += "{}, ".format(item.name)

                items_str += "and {}".format(self.items[-1].name)
            # one item
            elif len(self.items) == 1:
                opened_str = self.text["LOOK_ITEMS"]
                items_str += self.items[0].name
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
        else:
            self.echo(self.text["ALREADY_UNLOCKED"].format(name=self.name))


