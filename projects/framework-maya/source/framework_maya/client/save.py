# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
from framework_qt.client.save import QtSaveClientWidget
from framework_maya import utils as maya_utils


class MayaQtSaveClientWidget(QtSaveClientWidget):
    '''Client for doing an incremental save of Maya scene locally

    This is sample code that exists here for reference and not used by the current
    version of the framework.
    '''

    dcc_utils = maya_utils
