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
        super(Item, self).__init__(name, description, Item.DEFAULT_PROPERTIES,
            synonyms)
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

    def __init__(self, name, synonyms=(), description="", properties={}):
        super(Container, self).__init__(name, description,
            Container.DEFAULT_PROPERTIES, synonyms)
        self.properties.update(properties)
        self.items = []

        # EVENTS
        # player opened this container
        self.on_open = Event()