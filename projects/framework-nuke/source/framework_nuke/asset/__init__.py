# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from framework_core.asset import FtrackObjectManager
from framework_nuke.asset.dcc_object import NukeDccObject


class NukeFtrackObjectManager(FtrackObjectManager):
    '''
    NukeFtrackObjectManager class.
    Mantain the syncronization between asset_info and the ftrack information of
    the objects in the scene.
    '''

    DccObject = NukeDccObject

    def __init__(self, event_manager):
        '''
        Initialize NukeFtrackObjectManager with *event_manager*.

        *event_manager* instance of
        :class:`framework_core.event.EventManager`
        '''
        super(NukeFtrackObjectManager, self).__init__(event_manager)
