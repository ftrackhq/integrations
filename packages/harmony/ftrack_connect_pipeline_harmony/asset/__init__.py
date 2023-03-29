# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline.asset import FtrackObjectManager
from ftrack_connect_pipeline_harmony.asset.dcc_object import HarmonyDccObject


class HarmonyFtrackObjectManager(FtrackObjectManager):
    '''
    HarmonyFtrackObjectManager class.
    Mantain the syncronization between asset_info and the ftrack information of
    the objects in the scene.
    '''

    DccObject = HarmonyDccObject

    def __init__(self, event_manager):
        '''
        Initialize HarmonyFtrackObjectManager with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(HarmonyFtrackObjectManager, self).__init__(event_manager)
