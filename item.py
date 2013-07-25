# item.py
# objects that reside in a room

from .event import Event
from .echo import EchoMixin


class AbstractItem(EchoMixin):
    """
    base class for item
    doesn't contain any properties or event hooks
    """

    def __init__(self, name, synonyms=(), description=""):
        super(AbstractItem, self).__init__()

        # this must be unique to the room
        self._name = name
        self.description = description
        # other names that the item can be called
        # these must also be unique to the room
        self.synonyms = synonyms
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


    CRITERIA FOR PROPERTIES
    -intrinsic to the item; they are NOT relative to player
        -ex., a room does not have the property "entered" because
        it is relative to the player
    -immutable; cannot change within the course of the game
        -ex., a container does not have the property "opened" (it is a state)
    """

    def __init__(self, name, synonyms=(), description="", items=[], inventory=False,
        containable=True, container=False):
        super(Item, self).__init__(name, synonyms, description)

        #properties
        self._inventory = inventory
        self._containable = containable
        self._container = container

        self.owner = None # the container the item is in
        self._room = None
        self._player = None # the player whose inventory the item is in

        # EVENTS
        # player looked at this item
        self.on_look = Event()

    @property
    def inventory(self):
        return self._inventory

    @property
    def containable(self):
        return self._containable

    @property
    def container(self):
        return self._container

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

    TEXT = {
        "OPENED": "The {name} is open.",
        "CLOSED": "The {name} is closed.",
        "LOOK_ITEMS": "The {name} has these items inside it: {items}",
        "LOOK_EMPTY": "The {name} is open but it has nothing inside it.",
        "OPEN": "The {name} is now opened.",
        "ALREADY_OPEN": "The {name} is already open.",
        "OPEN_LOCKED": "The {name} is locked.",
        "CLOSE": "The {name} is now closed.",
        "ALREADY_CLOSED": "The {name} is already closed.",
        "UNLOCK": "The {name} is now unlocked.",
        "ALREADY_UNLOCKED": "The {name} is already unlocked.",
        "LOCK": "The {name} is now locked.",
        "ALREADY_LOCKED": "The {name} is already locked.",
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

    def __init__(self, name, synonyms=(), description="", items=[], opened=False,
        locked=False, inventory=False, containable=False):

        # containers can't be containable themselves (for now)
        # maybe add Russian doll-style recursive containers later?
        super(Container, self).__init__(name, synonyms, description,
            inventory, containable=False, container=True)

        # template strings for printing
        self.text.update(Container.TEXT)
        self._items = []
        self.insert_items(items)
        self._locked = locked
        self._opened = False if locked else opened

        # EVENTS
        # player opened this container
        self.on_open = Event()
        # player closed this container
        self.on_close = Event()
        # container was unlocked
        self.on_unlock = Event()
        # container was locked
        self.on_lock = Event()
        # item added to container
        self.on_add_item = Event()
        # item removed from container
        self.on_remove_item = Event()

    # opened is read-only
    @property
    def opened(self):
        return self._opened

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
        unlock the container
        """
        if self._locked:
            self._locked = False
            self.echo(self.text["UNLOCK"].format(name=self.name))
            self.on_unlock.trigger()
            # open the container too
            self.open()
        else:
            self.echo(self.text["ALREADY_UNLOCKED"].format(name=self.name))

    def lock(self):
        """
        lock container
        """
        if not self._locked:
            # close the container before locking it
            if self._opened:
                self.close()

            self._locked = True
            self.echo(self.text["LOCK"].format(name=self.name))
            self.on_lock.trigger()
        else:
            self.echo(self.text["ALREADY_LOCKED"].format(name=self.name))

    def add(self, item):
        """
        add item to container
        """
        if not item.owner == None:
            self.echo(self.text["ADD_CONTAINED"].format(item=item.name,
                container=item.owner.name))
            return

        if item in self._items:
            self.echo(self.text["ALREADY_ADDED"].format(name=self.name,
                item=item.name))
            return

        if not item._containable:
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

        item.owner = self
        self._items.append(item)
        self.echo(self.text["ADD"].format(name=self.name,
            item=item.name))
        self.on_add_item.trigger()

    def insert_item(self, item):
        """
        insert a single item to container
        """
        if not item in self._items:
            item.owner = self
            self._items.append(item)

    def insert_items(self, items):
        """
        this is used internally to manually add items to the container
        this is NOT called by the player; it does not print messages
        """
        for item in items:
            if not item in self._items:
                item.owner = self
                self._items.append(item)

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

        item.owner = None
        self._items.remove(item)
        self.echo(self.text["REMOVE"].format(name=self.name, item=item.name))
        self.on_remove_item.trigger()

    def erase_item(self, item):
        """
        like the remove() counterpart of insert()
        """
        if item in self._items:
            item.owner = None
            self._items.remove(item)

    def get(self, item_name):
        """
        get item by name
        """
        for item in self._items:
            if item.name == item_name:
                return item

        return None

