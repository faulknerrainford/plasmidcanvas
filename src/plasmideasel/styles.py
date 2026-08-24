from plasmideasel._utils import DEFAULT_LABEL_FONT_SIZE

'''
TODO:
- define arrow styles
    + broad
    + Narrow
    + pub
    + major
    + overlap
    + promoter

- define rectangle styles
    + full
    + empty
    + thin
    + boardered
    + pub
    + major

- all styles
    + text size
'''


class ArrowStyle(object):

    _ARROW_LABEL_FONT_SIZE = DEFAULT_LABEL_FONT_SIZE
    _ARROW_WIDTH = None
    _ARROW_LABEL_TYPE = None

    def __init__(self, label_size=DEFAULT_LABEL_FONT_SIZE):
        """

        Parameters
        ----------
        label_size
        """
        self.label_size = label_size
