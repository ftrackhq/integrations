# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect.qt import QtWidgets


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        '''Instantiate the tab widget.'''
        super(TabWidget, self).__init__(*args, **kwargs)
