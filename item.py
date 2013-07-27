# item.py
# objects that reside in a room

from .event import Event
from .echo import EchoMixin
from .text_template import TextTemplateMixin


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
        # set of custom actions that the player can do to the item
        # the key in the action dict is the keyword of the action
        # and the value is a tuple containing the method to call (val[0])
        # and its arguments (val[1])
        self._actions = {}

    # name property is read only
    @property
    def name(self):
        return self._name

    def __unicode__(self):
        return self.name.decode()

    def __str__(self):
        return self.name

    def add_action(self, action_name, action_method, action_args={}):
        """
        add/replace a custom action to the item
        """
        if hasattr(action_method, "__call__"):
            self._actions[action_name] = (action_method, action_args)
        else:
            raise TypeError("Action method is not callable")

    def remove_action(self, action_name):
        """
        remove a custom action
        """
        if action_name in self._actions:
            self._actions.pop(action_name, None)
        else:
            raise ValueError("{action} is not an action of this item".format(
                action=action_name))

    def get_action(self, action_name):
        """
        retrieve an action by its name
        """
        if action_name in self._actions:
            return self._actions[action_name]
        else:
            return None


class Item(AbstractItem, TextTemplateMixin):
    """
    objects that reside within the world


    CRITERIA FOR PROPERTIES
    -intrinsic to the item; they are NOT relative to player
        -ex., a room does not have the property "entered" because
        it is relative to the player
    -immutable; cannot change within the course of the game
        -ex., a container does not have the property "opened" (it is a state)
    """

    TEXT = {
        "USE": "You use the {item}.",
        "DESCRIPTION": "{description}"
    }

    def __init__(self, name, synonyms=(), description="", inventory=False,
        containable=True, container=False, text={}):

        super(Item, self).__init__(name, synonyms, description)

        #properties
        self._inventory = inventory
        self._containable = containable
        self._container = container

        self._owner = None # the container the item is in
        self._room = None
        self._player = None # the player whose inventory the item is in

        # update text templates
        self.update_text(Item.TEXT)
        self.update_text(text)

        # EVENTS
        # player looked at this item
        self.add_action("look", self.look)
        self.on_look = Event()
        # this is a dummy action; have subclasses override it
        # or have callbacks to it
        self.add_action("use", self.use)
        self.on_use = Event()

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
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, new_owner):
        self._owner = new_owner
        if new_owner is not None:
            self.player = new_owner.player
            self.room = new_owner.room

    @property
    def room(self):
        return self._room

    @room.setter
    def room(self, new_room):
        """
        set the room the item is in
        """
        # unsubscribe current room
        if self._room is not None:
            self.on_echo.unsubscribe(self._room.object_echo)

        # subscribe new room
        self._room = new_room
        # only if it's actually a room, though
        if new_room is not None:
            self.on_echo.subscribe(self._room.object_echo)

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, new_player):
        """
        set player who possesses the item
        """
        # unsubscribe current player
        if self._player is not None:
            self.on_echo.unsubscribe(self._player.object_echo)

        # subscribe new player
        self._player = new_player
        # only if it's actually a player, though
        if new_player is not None:
            self.on_echo.subscribe(self._player.object_echo)

    def context(self, **extra):
        context = super(Item, self).context(**extra)

        if self._room is None:
            room = self._player.location.name
        else:
            room = self._room.name

        context.update({
            "name": self._name,
            "description": self.description,
            "room": room
        })

        return context

    def look(self):
        """
        player looked at item
        """
        # print description
        self.echo(self.text("DESCRIPTION"))
        self.on_look.trigger()

    def use(self):
        """
        use the item
        """
        self.echo(self.text("USE", item=self.name))
        self.on_use.trigger()


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

    def __init__(self, name, synonyms=(), description="", items=[],
        opened=False, locked=False, inventory=False, containable=False,
        text={}):

        # containers can't be containable themselves (for now)
        # maybe add Russian doll-style recursive containers later?
        super(Container, self).__init__(name, synonyms, description,
            inventory=inventory, containable=False, container=True)

        self._items = []
        self._insert(items)
        self._locked = locked
        self._opened = False if locked else opened

        # template strings for printing
        self.update_text(Container.TEXT)
        self.update_text(text)

        # EVENTS
        # player opened this container
        self.add_action("open", self.open)
        self.on_open = Event()
        # player closed this container
        self.add_action("close", self.close)
        self.on_close = Event()
        # lock/unlock events are not actions because we don't want the player
        # to be able to manually lock/unlock containers
        # container was unlocked
        self.on_unlock = Event()
        # container was locked
        self.on_lock = Event()
        # item added to container
        self.on_add_item = Event()
        # item removed from container
        self.on_remove_item = Event()

    @property
    def items(self):
        return self._items

    @property
    def room(self):
        return self._room

    @room.setter
    def room(self, new_room):
        """
        set the room the item is in
        """
        # unsubscribe current room
        if self._room is not None:
            self.on_echo.unsubscribe(self._room.object_echo)

        # subscribe new room
        self._room = new_room
        # only if it's actually a room, though
        if new_room is not None:
            self.on_echo.subscribe(self._room.object_echo)

        # do the same for all the items in the container
        for item in self._items:
            item.room = new_room

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, new_player):
        """
        set player who possesses the item
        """
        # unsubscribe current player
        if self._player is not None:
            self.on_echo.unsubscribe(self._player.object_echo)

        # subscribe new player
        self._player = new_player
        # only if it's actually a player, though
        if new_player is not None:
            self.on_echo.subscribe(self._player.object_echo)

        # do the same for all the items in the container
        for item in self._items:
            item.player = new_player

    # opened is read-only
    @property
    def opened(self):
        return self._opened

    @property
    def locked(self):
        return self._locked

    def context(self, **extra):
        context = super(Container, self).context(**extra)

        items_str = ""

        # multiple items in container
        if len(self._items) > 1:
            for item in self._items[:-2]:
                items_str += "{}, ".format(item.name)

            items_str += "{} ".format(self._items[-2].name)
            items_str += "and {}".format(self._items[-1].name)
        # one item
        elif len(self._items) == 1:
            items_str += self._items[0].name

        context.update({
            "items": items_str
        })

        return context

    def look(self, describe_self=True, describe_items=True):
        """
        override Item.look() to include items inside the container if it is open
        """
        # print description
        if describe_self:
            self.echo(self.description)
            if self._opened:
                self.echo(self.text("OPENED"))
            else:
                self.echo(self.text("CLOSED"))

        # print items in the container if it is open
        if describe_items and self._opened:
            opened_str = ""

            # multiple items in container
            if len(self._items) > 1:
                self.echo(self.text("LOOK_ITEMS"))
            # one item
            elif len(self._items) == 1:
                self.echo(self.text("LOOK_ITEMS"))
            # no items
            else:
                self.echo(self.text("LOOK_EMPTY"))

        # send trigger
        self.on_look.trigger()

    def open(self):
        """
        player opened the container
        """
        if not self._opened:
            if not self._locked:
                self._opened = True
                self.echo(self.text("OPEN"))
                # you look inside the container when you open it
                # don't describe the container again, though
                self.look(describe_self=False)
                self.on_open.trigger()
            else:
                self.echo(self.text("OPEN_LOCKED"))
        else:
            self.echo(self.text("ALREADY_OPEN"))

    def close(self):
        """
        player closed the container
        """
        if self._opened:
            self._opened = False
            self.echo(self.text("CLOSE"))
            self.on_close.trigger()
        else:
            self.echo(self.text("ALREADY_CLOSED"))

    def unlock(self):
        """
        unlock the container
        """
        if self._locked:
            self._locked = False
            self.echo(self.text("UNLOCK"))
            self.on_unlock.trigger()
            # open the container too
            self.open()
        else:
            self.echo(self.text("ALREADY_UNLOCKED"))

    def lock(self):
        """
        lock container
        """
        if not self._locked:
            # close the container before locking it
            if self._opened:
                self.close()

            self._locked = True
            self.echo(self.text("LOCK"))
            self.on_lock.trigger()
        else:
            self.echo(self.text("ALREADY_LOCKED"))

    def add(self, item):
        """
        add item to container
        """
        if item.owner is not None:
            self.echo(self.text("ADD_CONTAINED", item=item.name,
                container=item.owner.name))
            return

        if item in self._items:
            self.echo(self.text("ALREADY_ADDED", item=item.name))
            return

        if not item._containable:
            self.echo(self.text("ADD_NOT_CONTAINABLE", item=item.name))
            return

        if self._locked:
            self.echo(self.text("ADD_LOCKED", item=item.name))
            return
        
        if not self._opened:
            self.echo(self.text("CLOSED"))
            return

        self._insert(item)
        self.echo(self.text("ADD", item=item.name))
        self.on_add_item.trigger()

    def _insert(self, items):
        """
        this is used internally to manually add items to the container
        this is NOT called by the player; it does not print messages
        """
        if not type(items) == list:
            items = [items]

        for item in items:
            if not item in self._items:
                # move item to the container's room, if it isn't
                if item.room is None and self.room is not None:
                    item.player._erase(item)
                    self.room.add(item)
                # move item to the player inventory, if it isn't
                elif item.player is None and self.player is not None:
                    item.room.remove(item)
                    self.player._insert(item)

                item.owner = self
                self._items.append(item)

    def remove(self, item):
        """
        remove item from container
        """
        if not item in self._items:
            self.echo(self.text("ALREADY_REMOVED", item=item.name))
            return

        if self._locked:
            self.echo(self.text("REMOVE_LOCKED", item=item.name))
            return

        if not self._opened:
            self.echo(self.text("CLOSED"))
            return
 
        self._erase(item)
        self.echo(self.text("REMOVE", item=item.name))
        self.on_remove_item.trigger()

    def _erase(self, item):
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


class Key(Item):
    """
    item that unlocks a container
    """

    TEXT = {
        "NO_CONTAINER_TO_OPEN": "{name} doesn't unlock anything.",
        "CONTAINER_NOT_IN_ROOM": "{name} doesn't open anything in the {room}."
    }

    def __init__(self, name, synonyms=(), description="",
        container_to_open=None, inventory=True, containable=True,
        container=False, text={}):

        super(Key, self).__init__(name, synonyms, description,
            inventory=inventory, containable=containable, container=container)

        self._container_to_open = None
        self.container_to_open = container_to_open

        # text templates
        self.update_text(Key.TEXT)
        self.update_text(text)

    @property
    def container_to_open(self):
        return self._container_to_open

    @container_to_open.setter
    def container_to_open(self, container):
        if container is None or isinstance(container, Container):
            self._container_to_open = container
        else:
            raise TypeError("Tried to set non-container as item to open")

    def use(self):
        if self._container_to_open is None:
            self.echo(self.text("NO_CONTAINER_TO_OPEN"))

        # key must be in the same room or in player's inventory to be used
        elif not self.room == self._container_to_open.room and \
            not self.player.location == self._container_to_open.room:

            if self.room is not None:
                item_room = self.room.name
            else:
                item_room = self.player.location.name

            self.echo(self.text("CONTAINER_NOT_IN_ROOM"))

        else:
            self._container_to_open.unlock()
            self.on_use.trigger()