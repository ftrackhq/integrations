# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_core.asset import FtrackObjectManager
from ftrack_framework_3dsmax.asset.dcc_object import MaxDccObject


class MaxFtrackObjectManager(FtrackObjectManager):
    '''
    MaxFtrackObjectManager class.
    Mantain the syncronization between asset_info and the ftrack information of
    the objects in the scene.
    '''

    DccObject = MaxDccObject

    def __init__(self, event_manager):
        '''
        Initialize MaxFtrackObjectManager with *event_manager*.

        *event_manager* instance of
        :class:`ftrack_framework_core.event.EventManager`
        '''
        super(MaxFtrackObjectManager, self).__init__(event_manager)
