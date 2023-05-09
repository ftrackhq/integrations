# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from framework_core.asset import FtrackObjectManager
from framework_maya.asset.dcc_object import MayaDccObject


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
        :class:`framework_core.event.EventManager`
        '''
        super(MayaFtrackObjectManager, self).__init__(event_manager)
