# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

try:
    from PySide6 import QtWidgets
except ImportError:
    from PySide2 import QtWidgets


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        '''Instantiate the tab widget.'''
        super(TabWidget, self).__init__(*args, **kwargs)
