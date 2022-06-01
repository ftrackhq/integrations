# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import logging

from ftrack_connect_pipeline_qt.client.save import QtSaveClientWidget
from ftrack_connect_pipeline_nuke.utils import custom_commands as nuke_utils


class NukeQtSaveClientWidget(QtSaveClientWidget):
    '''Client for doing an incremental save of Maya scene locally'''

    dcc_utils = nuke_utils
