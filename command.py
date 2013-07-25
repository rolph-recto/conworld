# command.py
# facilitate user interaction with the world

import re

from .echo import EchoMixin


class Command(EchoMixin):
    """
    user-specified tasks that interact with the world
    """

    # words that should be removed from a command string
    STOPWORDS = ["the", "a", "in", "at", "to"]

    def __init__(self, pattern, world=None):
        super(Command, self).__init__()

        self._pattern = pattern
        self.world = world

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

    def match(self, input):
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
            self.execute(**output.groupdict())
            return True
        else:
            return False

    def execute(self, **kwargs):
        """
        perform the command's task
        let subclasses override this
        """
        pass


class LookCommand(Command):
    """
    look at an item
    """

    PATTERN = r"look (?P<item_name>[\w\s\d]+)"
    TEXT = {
        "NO_ITEM": "You don't see a {item}."
    }

    def __init__(self, world=None):
        super(LookCommand, self).__init__(LookCommand.PATTERN, world)

    def execute(self, item_name):
        # check if the item is in the current room
        item = self.world.player.location.get_item(item_name)

        if not item == None:
            if ((not item.owner == None) and item.owner.opened) or \
            item.owner == None:
                item.look()

            else:
                self.echo(LookCommand.TEXT["NO_ITEM"].format(item=item_name))

        else:
            self.echo(LookCommand.TEXT["NO_ITEM"].format(item=item_name))


