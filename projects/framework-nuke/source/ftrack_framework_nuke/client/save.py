# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging

from ftrack_framework_qt.client.save import QtSaveClientWidget
from ftrack_framework_nuke import utils as nuke_utils


class NukeQtSaveClientWidget(QtSaveClientWidget):
    '''Client for doing an incremental save of Nuke script locally

    This is sample code that exists here for reference and not used by the current
    version of the framework.
    '''

    dcc_utils = nuke_utils
