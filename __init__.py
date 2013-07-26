# __init__.py
# conworld package

# path directions
DIRECTIONS = ("north", "south", "east", "west", "up", "down")
DIRECTION_SYNONYMS = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
    "u": "up",
    "d": "down"
}

# words that should be removed from a command string
STOPWORDS = ["the", "a", "in", "at", "to", "room", "around"]

def enumerate_items(items):
    """
    list items in a string
    ex. ["dog", "cat", "mouse"] returns "dog, cat, and mouse"
    """
    items_str = ""
    # multiple items in container
    if len(items) > 1:
        for item in items[:-2]:
            items_str += "{}, ".format(item)

        items_str += "{} ".format(items[-2])
        items_str += "and {}".format(items[-1])
    # one item
    elif len(items) == 1:
        items_str += items[0]
    
    return items_str