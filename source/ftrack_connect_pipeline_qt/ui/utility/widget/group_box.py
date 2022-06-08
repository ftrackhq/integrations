# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets


class GroupBox(QtWidgets.QGroupBox):
    '''Group box widget wrapper'''

    def __init__(self, title=None, parent=None):
        super(GroupBox, self).__init__(title, parent=parent)
        # Mitigate Maya style issues
        self.setStyle(QtWidgets.QStyleFactory.create("plastique"))
