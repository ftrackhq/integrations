# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline.asset import FtrackObjectManager
from ftrack_connect_pipeline_maya.asset.dcc_object import MayaDccObject


class MayaFtrackObjectManager(FtrackObjectManager):
    '''
    MayaFtrackObjectManager class.
    Mantain the syncronization between asset_info and the ftrack information of
    the objects in the scene.
    '''

    DccObject = MayaDccObject

    def __init__(self, event_manager):
        '''
        Initialize MayaFtrackObjectManager with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_connect_pipeline.event.EventManager`
        '''
        super(MayaFtrackObjectManager, self).__init__(event_manager)
