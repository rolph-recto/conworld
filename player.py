# player.py
# a bad, bad person

from .event import Event
from .echo import EchoMixin


class Player(EchoMixin):
    """
    represents user
    """

    TEXT = {
        "TAKE": "You take the {item} and put it in your inventory.",
        "TAKE_IN_LOCKED_CONTAINER": ("The {item} is locked inside "
            "the {container}."),
        "TAKE_NOT_INVENTORY": "You can't take the {item}.",
        "ALREADY_TAKEN": "The {item} is already in your inventory.",
        "DISCARD": "You discard the {item} and leave it in the {room}.",
        "ALREADY_DISCARDED": "The {item} is not in your inventory.",
        "NO_PATH": "You can't go {direction}.",
        "PATH_BLOCKED": "The path {direction}ward is blocked."
    }

    def __init__(self, start_location=None):
        super(Player, self).__init__()

        # list of items a player has
        self._inventory = []

        # location of player (room that player is currently in)
        self.location = start_location

        # template strings for printing
        self.text = {}
        self.text.update(Player.TEXT)

        # EVENTS
        # player added an item to inventory
        self.on_take_item = Event()
        # player discards item from inventory
        self.on_discard_item = Event()
        # player moves to another room
        self.on_move = Event()

    def take(self, item):
        """
        add an item to the inventory
        """
        if not item.inventory:
            self.echo(self.text["TAKE_NOT_INVENTORY"].format(item=item.name))
            return

        if not item.owner == None and item.owner.locked:
            self.echo(self.text["TAKE_IN_LOCKED_CONTAINER"].format(
                item=item.name, container=item.owner.name))

        if item in self._inventory:
            self.echo(self.text["ALREADY_TAKEN"].format(item=item.name))
            return

        # if the item is in the container, open the container and
        # take the item out of it
        if not item.owner == None:
            if not item.owner.opened:
                item.owner.open()

            item.owner.remove(item)

        # the item is "roomless" when it is in the inventory
        item.room.remove_item(item)
        item.player = self
        self._inventory.append(item)
        self.echo(self.text["TAKE"].format(item=item.name))
        self.on_take_item.trigger()

    def discard(self, item):
        """
        remove an item from inventory
        """
        if item in self._inventory:
            # put item back into room when it is discarded
            self.location.add_item(item)
            item.player = None
            self._inventory.remove(item)
            self.on_discard_item.trigger()
            self.echo(self.text["DISCARD"].format(item=item.name,
                room=self.location.name))
        else:
            self.echo(self.text["DISCARD"].format(item=item.name))

    def get_item(self, item_name):
        """
        get item from inventory by its name
        """
        for item in self._inventory:
            if item.name == item_name:
                return item

        return None

    def move(self, direction):
        """
        move to another room
        """
        path = self.location.get_path(direction)
        if not path == None:
            if not path.blocked:
                # exit current location
                self.location.exit()

                # enter new location
                self.location = path.destination
                self.location.enter()

                self.on_move.trigger()
            else:
                self.echo(self.text["PATH_BLOCKED"].format(direction=direction))
        else:
            self.echo(self.text["NO_PATH"].format(direction=direction))

    def look(self):
        """
        look around (equivalent to looking around the current location)
        """
        self.location.look()

    def object_echo(self, msg):
        """
        relay inventory item messages to player echo callbacks
        """
        self.echo(msg)



