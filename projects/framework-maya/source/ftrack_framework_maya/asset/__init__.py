# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core.asset import FtrackObjectManager
from ftrack_framework_maya.asset.dcc_object import MayaDccObject


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
        :class:`ftrack_framework_core.event.EventManager`
        '''
        super(MayaFtrackObjectManager, self).__init__(event_manager)
