# command_kernel.py

from .echo import EchoMixin


class CommandKernel(EchoMixin):
    """
    facilitate between commands and the world
    """

    TEXT = {
        "NO_COMMAND": "I don't understand what you mean."
    }

    def __init__(self, world, commands=[]):
        super(CommandKernel, self).__init__()

        self._commands = []
        self.add_commands(commands)

    def add_command(self, command):
        """
        add a command
        """
        self.add_commands([command])

    def add_commands(self, commands):
        """
        add multiple commands
        """
        for command in commands:
            if not command in self._commands:
                command.on_echo.subscribe(self.command_echo)
                self._commands.append(command)
            else:
                raise RuntimeError("Command is already in the kernel")

    def command_echo(self, msg):
        """
        relay command messages to the IO driver
        """
        self.echo(msg)

    def input(self, world, input):
        """
        feed the input to the list of commands
        """
        for command in self._commands:
            # once we have a match, stop
            if command.match(world, input):
                return

        # if we reach here, that means the input matched no command
        self.echo(CommandKernel.TEXT["NO_COMMAND"].format(input=input))
