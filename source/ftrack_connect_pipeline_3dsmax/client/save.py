# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_qt.client.save import QtSaveClientWidget
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as 3dsmax_utils


class MaxQtSaveClientWidget(QtSaveClientWidget):
    '''Client for doing an incremental save of Max scene locally

    This is sample code that exists here for reference and not used by the current
    version of the framework.
    '''

    dcc_utils = 3dsmax_utils
