# command.py
# facilitate user interaction with the world

import re

from . import DIRECTIONS, DIRECTION_SYNONYMS
from .echo import EchoMixin


class Command(EchoMixin):
    """
    user-specified tasks that interact with the world
    """

    # words that should be removed from a command string
    STOPWORDS = ["the", "a", "in", "at", "to", "room", "around"]

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

    @classmethod
    def _preprocess(cls, input):
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
            if not word in Command.STOPWORDS])
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
        input = Command._preprocess(input)
        cmd_pattern = re.compile(self._pattern)
        output = cmd_pattern.search(input)

        # if the command pattern matches, execute the command!
        if not output == None:
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

    PATTERN = r"^look$"

    def __init__(self):
        super(LookRoomCommand, self).__init__("look room",
            LookRoomCommand.PATTERN)

    def execute(self, world):
        # look at the player's current location
        world.player.location.look()


class LookItemCommand(Command):
    """
    look at an item
    """

    PATTERN = r"look (?P<item_name>[\w\s\d]+)"
    TEXT = {
        "NO_ITEM": "You don't see a {item}."
    }

    def __init__(self):
        super(LookItemCommand, self).__init__("look item",
            LookItemCommand.PATTERN)

    def execute(self, world, item_name):
        # check if the item is in the current room
        item = world.player.location.get_item(item_name)

        if not item == None:
            if ((not item.owner == None) and item.owner.opened) or \
            item.owner == None:
                item.look()

            else:
                self.echo(LookItemCommand.TEXT["NO_ITEM"]
                    .format(item=item_name))

        else:
            self.echo(LookItemCommand.TEXT["NO_ITEM"].format(item=item_name))


class MoveCommand(Command):
    """
    move to another room
    """

    PATTERN = r"(move|go) (?P<direction>[\w]+)"
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

    PATTERN = r"take (?P<item_name>[\w\s\d]+)"
    TEXT = {
        "NO_ITEM": "There is no {item} in the {room}."
    }

    def __init__(self):
        super(TakeCommand, self).__init__("take", TakeCommand.PATTERN)

    def execute(self, world, item_name):
        # check if the item is in the current room
        item = world.player.location.get_item(item_name)

        if not item == None:
            world.player.take(item)
        else:
            self.echo(TakeCommand.TEXT["NO_ITEM"].format(
                item=item_name, room=world.player.location.name))


class DiscardCommand(Command):
    """
    discard an item from the inventory
    """

    PATTERN = r"(discard|throw|throw away) (?P<item_name>[\w\s\d]+)"
    TEXT = {
        "NO_ITEM": "There is no {item} in your inventory."
    }

    def __init__(self):
        super(DiscardCommand, self).__init__("discard", DiscardCommand.PATTERN)

    def execute(self, world, item_name):
        # check if item is in player's inventory
        item = world.player.get_item(item_name)

        if not item == None:
            world.player.discard(item)
        else:
            self.echo(DiscardCommand.TEXT["NO_ITEM"].format(item=item_name))