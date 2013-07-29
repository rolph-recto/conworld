# path.py
# path class

from .event import Event
from .echo import EchoMixin
from .text_template import TextTemplateMixin


class Path(EchoMixin, TextTemplateMixin):
    """
    path from one room to another
    """

    TEXT = {
        "BLOCK": "The {path} to the {destination} is now blocked.",
        "ALREADY_BLOCKED": ("The {path} to the {destination} "
            "is already blocked."),
        "UNBLOCK": "The {path} to the {destination} is now unblocked.",
        "ALREADY_UNBLOCKED": ("The {path} to the {destination} "
            "is already unblocked.")
    }

    def __init__(self, name, source, destination, blocked=False, text={}):

        super(Path, self).__init__()

        self._name = name
        self._source = source
        self._destination = destination
        self._blocked = blocked
        # verb used to signify the path is blocked or unblocked
        # (ex. the gate is "opened" or "closed"
        # we use arguments for the verbs because subclassing path
        # just to change the verbs would be a little excessive
        self.update_text(Path.TEXT)
        self.update_text(text)

        # EVENTS
        # path was blocked
        self.on_block = Event()
        self.on_unblock = Event()

    @property
    def name(self):
        return self._name

    @property
    def source(self):
        return self._source

    @property
    def destination(self):
        return self._destination

    @property
    def blocked(self):
        return self._blocked

    def context(self, **extra):
        context = super(Path, self).context(**extra)
        context.update({
            "path": self._name,
            "destination": self._destination.name
        })
        return context

    def block(self, echo=True):
        """
        block the path
        """
        if not self._blocked:
            self._blocked = True
            if echo: self.echo(self.text("BLOCK"))
            self.on_block.trigger()
        else:
            self.echo(self.text("ALREADY_UNBLOCKED"))

    def unblock(self, echo=True):
        """
        unblock the path
        """
        if self._blocked:
            self._blocked = False
            if echo: self.echo(self.text("UNBLOCK"))
            self.on_unblock.trigger()
        else:
            self.echo(self.text("ALREADY_BLOCKED"))

    def toggle(self, echo=True):
        """
        toggle between blocked and unblocked
        """
        if self._blocked:
            self.unblock(echo)
        else:
            self.block(echo)