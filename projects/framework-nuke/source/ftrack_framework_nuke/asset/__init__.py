# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_asset_manager.asset import FtrackObjectManager
from ftrack_framework_nuke.asset.dcc_object import NukeDccObject


class NukeFtrackObjectManager(FtrackObjectManager):
    '''
    NukeFtrackObjectManager class.
    Mantain the syncronization between asset_info and the ftrack information of
    the objects in the scene.
    '''

    DccObject = NukeDccObject

    def __init__(self, session):
        '''
        Initialize NukeFtrackObjectManager with *session*.

        *session* instance of ftrack_api.Session
        '''
        super(NukeFtrackObjectManager, self).__init__(session)
