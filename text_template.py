# text_template.py
# text template mixin


class TextTemplateMixin(object):
    """
    provides functionality for customizing text (usually for echoing)
    """

    def __init__(self, text={}):
        self._text = {}
        self._text.update(text)

        # call next mixin constructor, if it exists
        # this makes multiple inheritance work
        super(TextTemplateMixin, self).__init__()

    def update_text(self, text):
        self._text.update(text)

    def context(self, **extra):
        """
        return the content of the template
        subclasses should override this, obviously
        """
        context = {}
        context.update(extra)
        return context

    def text(self, key, **extra):
        """
        retrieve a text with a built-in context
        """

        if key in self._text:
            return self._text[key].format(**self.context(**extra))
        else:
            raise KeyError("Template dictionary has no key {}".format(key))