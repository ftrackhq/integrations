# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_asset_manager.asset.ftrack_object_manager import (
    FtrackObjectManager,
)
from ftrack_framework_maya.asset.dcc_object import MayaDccObject


class MayaFtrackObjectManager(FtrackObjectManager):
    '''
    MayaFtrackObjectManager class.
    Mantain the syncronization between asset_info and the ftrack information of
    the objects in the scene.
    '''

    DccObject = MayaDccObject

    def __init__(self, session):
        '''
        Initialize MayaFtrackObjectManager with *session*.

        *session* instance of ftrack_api.Session
        '''
        super(MayaFtrackObjectManager, self).__init__(session)
