# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
from ftrack_connect_pipeline_qt.client.save import QtSaveClient
from ftrack_connect_pipeline_maya.utils import custom_commands as maya_utils


class QtMayaSaveClient(QtSaveClient):
    '''Client for doing an incremental save of Maya scene locally'''

    dcc_utils = maya_utils
