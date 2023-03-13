# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets


class ScrollArea(QtWidgets.QScrollArea):
    '''Scroll area widget wrapper'''

    def __init__(self, parent=None):
        super(ScrollArea, self).__init__(parent=parent)
        # Mitigate Maya style issues
        self.setStyle(QtWidgets.QStyleFactory.create("plastique"))
