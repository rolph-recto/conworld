# io_driver.py
# bridge between world (game state) and user


class IODriver(object):
    """
    relays input and output between World and user
    """

    def __init__(self, world, kernel):
        # world
        self._world = world
        # listen to echoes from world
        self._world.on_echo.subscribe(self.world_echo)

        # command kernel
        self._kernel = kernel
        # listen to echoes from the kernel
        self._kernel.on_echo.subscribe(self.kernel_echo)

        # list of strings emitted by world
        self._outstream = []

    # world property is read only
    @property
    def world(self):
        return self._world

    # kernel property is read only
    @property
    def kernel(self):
        return self._kernel

    def world_echo(self, msg):
        """
        capture messages from world into output stream
        """
        self._outstream.append(msg)

    def kernel_echo(self, msg):
        """
        capture messages from command kernel
        """
        self._outstream.append(msg)

    def flush_output(self):
        """
        flush output stream
        """
        self._outstream = []

    def process(self, input_str):
        """
        feed input into world and return output
        """
        self._kernel.input(input_str)
        output = self._outstream[:]
        self.flush_output()

        return output




