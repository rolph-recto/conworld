# world.py
# collection of rooms

from .echo import EchoMixin


class AbstractWorld(EchoMixin):
    """
    base class for world
    """

    def __init__(self, rooms=[]):
        super(AbstractWorld, self).__init__()
        
        self._rooms = []
        self.add_rooms(rooms)

    def add_room(self, room):
        """
        add a room to the world
        """
        self.add_rooms([room])

    def add_rooms(self, rooms):
        """
        add multiple rooms to the world
        """
        for room in rooms:
            if not room in self._rooms:
                room.world = self
                self._rooms.append(room)
            else:
                raise RuntimeError("{room} is already in world"
                    .format(room=room.name))

    def remove_room(self, room):
        """
        remove a room from the world
        """
        if room in self._rooms:
            room.world = None
            self._rooms.remove(room)
        else:
            raise RuntimeError("{room} is not in the world"
                .format(room=room.name))

    def room_echo(self, msg):
        """
        relay room messages to world echo callbacks (ex. IO driver)
        """
        self.echo(msg)

    def player_echo(self, msg):
        """
        relay messages from player to world echo callbacks (ex. IO driver)
        """
        self.echo(msg)


class World(AbstractWorld):
    """
    collection of rooms
    """

    def __init__(self, player, rooms=[]):
        super(World, self).__init__(rooms)
        self._player = player
        self._player.on_echo.subscribe(self.player_echo)

    # player property is read-only
    @property
    def player(self):
        return self._player

    def start(self):
        """
        start game; have player enter its current location
        """
        self._player.location.enter()