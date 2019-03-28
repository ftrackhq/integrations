#! /usr/bin/env python
# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import sys

deps_paths = os.environ.get('PYTHONPATH', '').split(os.pathsep)
for path in deps_paths:
    sys.path.append(path)


from QtExt import QtGui
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.client import BaseQtPipelineWidget


class QtPipelineLoaderWidget(BaseQtPipelineWidget):
    '''
    Base load widget class.
    '''
    def __init__(self, ui, host, hostid=None, parent=None):

        super(QtPipelineLoaderWidget, self).__init__(ui, host, hostid, parent=parent)
        self.setWindowTitle('Standalone Pipeline Loader')


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = QtPipelineLoaderWidget(ui=constants.UI, host=constants.HOST)
    wid.show()
    sys.exit(app.exec_())
