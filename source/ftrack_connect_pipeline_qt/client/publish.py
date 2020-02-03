#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import sys


deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)

from Qt import QtWidgets
import ftrack_api

QtWidgets.QApplication.setStyle('plastique')

from ftrack_connect_pipeline_qt.client import QtClient
from ftrack_connect_pipeline import constants, event
from ftrack_connect_pipeline_qt import constants as qt_contants


class QtPublisherClient(QtClient):
    '''
    Base load widget class.
    '''
    def __init__(self, event_manager, ui, parent=None):

        super(QtPublisherClient, self).__init__(event_manager, ui, parent=parent)
        self.setWindowTitle('Standalone Pipeline Publisher')


if __name__ == '__main__':
    session = ftrack_api.Session(auto_connect_event_hub=False)
    event_manager = event.EventManager(
        session=session, mode=constants.LOCAL_EVENT_MODE
    )
    app = QtWidgets.QApplication(sys.argv)
    wid = QtPublisherClient(event_manager, ui=[qt_contants.UI])
    wid.show()
    sys.exit(app.exec_())
