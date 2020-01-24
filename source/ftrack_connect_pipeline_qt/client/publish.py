#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import sys

from Qt import QtWidgets
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.client import QtClient


class QtPublisherClient(QtClient):
    '''
    Base load widget class.
    '''
    def __init__(self, event_manager, ui, parent=None):

        super(QtPublisherClient, self).__init__(event_manager, ui, parent=parent)
        self.setWindowTitle('Standalone Pipeline Publisher')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    #app.setStyle(QtWidgets.QStyleFactory.create('Fusion'))
    wid = QtPublisherClient(ui=constants.UI)
    wid.show()
    sys.exit(app.exec_())
