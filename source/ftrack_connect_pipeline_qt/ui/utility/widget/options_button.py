# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack


from Qt import QtCore, QtWidgets


class OptionsButton(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super(OptionsButton, self).__init__(parent=parent)
