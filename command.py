# command.py
# facilitate user interaction with the world

import re

from . import DIRECTIONS, DIRECTION_SYNONYMS, STOPWORDS, enumerate_items
from .echo import EchoMixin


class Command(EchoMixin):
    """
    user-specified tasks that interact with the world
    """

    def __init__(self, name, pattern):
        super(Command, self).__init__()

        self._pattern = pattern
        self._name = name

    @property
    def name(self):
        return self._name

    def __unicode__(self):
        return self._name.decode()

    def __str__(self):
        return self._name

    def _preprocess(self, input, stopwords=STOPWORDS):
        """
        clean up text before matching it with the command pattern
        this makes the command string patterns much simpler
        """

        # set to lowercase
        result = input.lower()
        # strip punctuation
        result = re.sub(r"[`~!@#$%^&*()-=_+,./<>?;':\"\[\]{}\|]", "", result)
        # remove stopwords
        result = " ".join([word for word in result.split()
            if not word in stopwords])
        # strip of leading / trailing whitespace
        result = result.strip()
        # normalize whitespace (convert sequence of spaces to 1 space)
        result = re.sub(r"[\s]{2,}", " ", result)

        return result

    def match(self, world, input):
        """
        check if the user input matches the command string pattern
        returns either true if the pattern matches and the command is executed
        or false if the pattern doesn't match
        """
        input = self._preprocess(input)
        cmd_pattern = re.compile(self._pattern)
        output = cmd_pattern.search(input)

        # if the command pattern matches, execute the command!
        if output is not None:
            self.execute(world, **output.groupdict())
            return True
        else:
            return False

    def execute(self, world, **kwargs):
        """
        perform the command's task
        let subclasses override this
        """
        pass


class LookRoomCommand(Command):
    """
    look at a room
    """

    PATTERN = r"^(look|view)$"

    def __init__(self):
        super(LookRoomCommand, self).__init__("look room",
            LookRoomCommand.PATTERN)

    def execute(self, world):
        # look at the player's current location
        world.player.location.look()


class MoveCommand(Command):
    """
    move to another room
    """

    PATTERN = r"^(move|go) (?P<direction>[\w]+)"
    TEXT = {
        "NO_DIRECTION": "{direction} is not a direction."
    }

    def __init__(self):
        super(MoveCommand, self).__init__("move", MoveCommand.PATTERN)

    def execute(self, world, direction):
        if direction in DIRECTIONS:
            world.player.move(direction)
        elif direction in DIRECTION_SYNONYMS:
            world.player.move(DIRECTION_SYNONYMS[direction])
        else:
            self.echo(MoveCommand.TEXT["NO_DIRECTION"].format(
                direction=direction))


class TakeCommand(Command):
    """
    take an item and put it in the inventory
    """

    PATTERN = r"^take (?P<item_name>[\w\s\d]+)"
    TEXT = {
        "ALREADY_IN_INVENTORY": "The {item} is already in your inventory.",
        "NO_ITEM": "There is no {item} in the {room}."
    }

    def __init__(self):
        super(TakeCommand, self).__init__("take", TakeCommand.PATTERN)

    def execute(self, world, item_name):
        # check if the item isn't alerady in the player's inventory
        if world.player.get(item_name) is not None:
            self.echo(TakeCommand.TEXT["ALREADY_IN_INVENTORY"].format(
                item=item_name))
        else:
            # check if the item is in the current room
            item = world.player.location.get(item_name)

            if item is not None:
                world.player.take(item)
            else:
                self.echo(TakeCommand.TEXT["NO_ITEM"].format(
                    item=item_name, room=world.player.location.name))


class DiscardCommand(Command):
    """
    discard an item from the inventory
    """

    PATTERN = r"^(discard|throw away|throw) (?P<item_name>[\w\s\d]+)"
    TEXT = {
        "NO_ITEM": "There is no {item} in your inventory."
    }

    def __init__(self):
        super(DiscardCommand, self).__init__("discard", DiscardCommand.PATTERN)

    def execute(self, world, item_name):
        # check if item is in player's inventory
        item = world.player.get(item_name)

        if item is not None:
            world.player.discard(item)
        else:
            self.echo(DiscardCommand.TEXT["NO_ITEM"].format(item=item_name))


class PutCommand(Command):
    """
    put an item in a container
    """
    # use custom stopword list -- omit "in" because we use that in the pattern
    CUSTOM_STOPWORDS = ["the", "a", "at", "to", "room", "around"]
    PATTERN = (r"^(put|place) (?P<item_name>[\w\d\s]+) in "
        r"(?P<container_name>[\w\d\s]+)")
    TEXT = {
        "NO_ITEM": "There is no {item} in the {room} or in your inventory.",
        "NO_CONTAINER": ("There is no {container} in the {room}"
            " or in your inventory."),
        "NOT_CONTAINER": "{container} is not a container."
    }

    def __init__(self):
        super(PutCommand, self).__init__("put", PutCommand.PATTERN)

    def _preprocess(self, input):
        """
        override Command._preprocess because we need a custom stopwords list
        """
        return super(PutCommand, self)._preprocess(input,
            stopwords=PutCommand.CUSTOM_STOPWORDS)

    def execute(self, world, item_name, container_name):
        # find item in room or in player's inventory
        item = world.player.location.get(item_name)
        if item is None:
            item = world.player.get(item_name)

        # find container in room or in player's inventory
        container = world.player.location.get(container_name)
        if container is None:
            container = world.player.get(container_name)

        # success
        if item is not None and container is not None:
            if container.container:
                container.add(item)
            else:
                self.echo(PutCommand.TEXT["NOT_CONTAINER"].format(
                    container=container_name))

        # item doesn't exist
        elif item is None:
            self.echo(PutCommand.TEXT["NO_ITEM"].format(item=item_name,
                room=world.player.location.name))
        # container doesn't exist
        else:
            self.echo(PutCommand.TEXT["NO_CONTAINER"].format(
                container=container_name, room=world.player.location.name))


class RemoveCommand(Command):
    """
    remove an item from a container
    """
    PATTERN = (r"^remove (?P<item_name>[\w\d\s]+) (out of|from) "
        r"(?P<container_name>[\w\d\s]+)")
    TEXT = {
        "NO_ITEM": "There is no {item} in the {room} or in your inventory.",
        "NO_CONTAINER": "{item} is not in {container}."
    }

    def __init__(self):
        super(RemoveCommand, self).__init__("remove", RemoveCommand.PATTERN)

    def execute(self, world, item_name, container_name):
        # find item in room or in player's inventory
        item = world.player.location.get(item_name)
        if item is None:
            item = world.player.get(item_name)

        if item is None:
            self.echo(RemoveCommand.TEXT["NO_ITEM"].format(item=item_name,
                room=world.player.location.name))

        elif item.owner is None or not item.owner.name == container_name:
            self.echo(RemoveCommand.TEXT["NO_CONTAINER"].format(item=item_name,
                container=container_name))

        else:
            item.owner.remove(item)


class InventoryCommand(Command):
    """
    view the player inventory
    """

    PATTERN = r"^inventory$"
    TEXT = {
        "INVENTORY": "You have the following items in your inventory: {items}",
        "NO_ITEMS": "You have no items in your inventory."
    }

    def __init__(self):
        super(InventoryCommand, self).__init__("inventory",
            InventoryCommand.PATTERN)

    def execute(self, world):
        # get player inventory
        # only display items not stored in containers
        items = [item.name for item in world.player.inventory
            if item.owner is None]

        if len(items) >= 1:
            self.echo(InventoryCommand.TEXT["INVENTORY"].format(
                items=enumerate_items(items)))
        else:
            self.echo(InventoryCommand.TEXT["NO_ITEMS"])


class ActionCommand(Command):
    """
    general command for interacting with objects
    -this is very powerful! examples of commands that can use this class include
    "look", open", and "close"
    -in general, commands that only need the action and item (no arguments like
        "put the candle in the chest") can use this class

    ADD THIS LAST TO THE KERNEL OR ELSE IT WILL OVERRIDE THE OTHER COMMANDS
    """

    PATTERN = r"(?P<action_name>[\w]+) (?P<item_name>[\w\s\d]+)"
    TEXT = {
        "NO_ITEM": "There is no {item} in the {room} or in your inventory.",
        "NO_COMMAND": "You can't {action} the {item}."
    }

    def __init__(self):
        super(ActionCommand, self).__init__("action", ActionCommand.PATTERN)

    def execute(self, world, action_name, item_name):
        # fetch item from current room or in player's inventory
        item = world.player.location.get(item_name)
        if item is None:
            item = world.player.get(item_name)


        if item is None:
            self.echo(ActionCommand.TEXT["NO_ITEM"].format(item=item_name,
                room=world.player.location.name))
        else:
            action = item.get_action(action_name)

            if action is None:
                self.echo(ActionCommand.TEXT["NO_COMMAND"].format(
                    action=action_name, item=item_name))
            # call the action method!
            else:
                func = action[0]
                # args is a keyword dictionary of arguments
                args = action[1]
                func(**args)