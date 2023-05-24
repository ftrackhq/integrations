# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_framework_core.asset import FtrackObjectManager
from ftrack_framework_houdini.asset.dcc_object import HoudiniDccObject


class HoudiniFtrackObjectManager(FtrackObjectManager):
    '''
    HoudiniFtrackObjectManager class.
    Mantain the syncronization between asset_info and the ftrack information of
    the objects in the scene.
    '''

    DccObject = HoudiniDccObject

    def __init__(self, event_manager):
        '''
        Initialize HoudiniFtrackObjectManager with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_framework_core.event.EventManager`
        '''
        super(HoudiniFtrackObjectManager, self).__init__(event_manager)
