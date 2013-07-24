# event.py
# event handling and callbaks

class Event(object):
    """
    handles event triggering and callbacks 
    """

    def __init__(self):
        self._callbacks = []

    def __call__(self, callback):
        """
        allows event object to be used as a decorator and subscribe callbacks
        """
        self.subscribe(callback)

    def subscribe(self, callback):
        """
        add a callback
        """
        if not callback in self._callbacks:
            self._callbacks.append(callback)
        else:
            raise RuntimeError("Callback is already subscribed to event")

    def unsubscribe(self, callback):
        """
        remove a callback
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
        else:
            raise RuntimeError("Callback is not subscribed to event")

    def trigger(self, *args, **kwargs):
        """
        call all callbacks
        """
        for callback in self._callbacks:
            callback(*args, **kwargs)
