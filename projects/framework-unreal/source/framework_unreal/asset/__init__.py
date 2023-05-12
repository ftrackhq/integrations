# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from framework_core.asset import FtrackObjectManager

from framework_unreal.asset.dcc_object import UnrealDccObject


class UnrealFtrackObjectManager(FtrackObjectManager):
    '''
    UnrealFtrackObjectManager class.
    Mantain the syncronization between asset_info and the ftrack information of
    the objects in the scene.
    '''

    DccObject = UnrealDccObject

    def __init__(self, event_manager):
        '''
        Initialize UnrealFtrackObjectManager with *event_manager*.

        *event_manager* instance of
        :class:`framework_core.event.EventManager`
        '''
        super(UnrealFtrackObjectManager, self).__init__(event_manager)
