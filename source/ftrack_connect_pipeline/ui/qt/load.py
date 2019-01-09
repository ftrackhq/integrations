#! /usr/bin/env python

import sys

from QtExt import QtWidgets, QtGui, QtCore

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.ui.base.load import BaseLoadUiPipeline
from ftrack_connect_pipeline.ui.qt import BaseQtPipelineWidget


class QtPipelineLoaderWidget(BaseLoadUiPipeline, BaseQtPipelineWidget):

    def __init__(self, host=None, parent=None):
        super(QtPipelineLoaderWidget, self).__init__(parent=None)
        self.setWindowTitle('Standalone Pipeline Loader')
        self.stage_type = constants.LOAD


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wid = QtPipelineLoaderWidget()
    wid.show()
    sys.exit(app.exec_())
