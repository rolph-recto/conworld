# command.py
# facilitate user interaction with the world

import re

from .echo import EchoMixin


class Command(EchoMixin):
    """
    user-specified tasks that interact with the world
    """

    # words that should be removed from a command string
    STOPWORDS = ["the", "a", "in"]

    def __init__(self, pattern, world):
        super(Command, self).__init__()

        self._pattern = pattern
        self._world = world


    @classmethod
    def _preprocess(cls, input):
        """
        clean up text before matching it with the command pattern
        this makes the command string patterns much simpler
        """

        # set to lowercase
        result = input.lower()
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
        else:
            return False

    def execute(self, **kwargs):
        """
        perform the command's task
        let subclasses override this
        """
        pass