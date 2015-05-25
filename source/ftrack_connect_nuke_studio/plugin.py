# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import FnAssetAPI

import ftrack_connect_foundry.plugin
import ftrack_connect_nuke_studio.bridge
import ftrack_connect_nuke_studio.manager
import ftrack_connect.ui.theme
import ftrack_connect.event_hub_thread


# Start thread to handle events from ftrack.
eventHubThread = ftrack_connect.event_hub_thread.EventHubThread()
eventHubThread.start()

# Import crew hub to instantiate a global crew hub.
import ftrack_connect_nuke_studio.crew_hub

ftrack_connect.ui.theme.applyFont()


class Plugin(ftrack_connect_foundry.plugin.Plugin):
    '''ftrack manager plugin for NUKE STUDIO.'''

    @classmethod
    def _initialiseBridge(cls):
        '''Initialise bridge.'''
        if cls._bridge is None:
            cls._bridge = ftrack_connect_nuke_studio.bridge.Bridge()

    @classmethod
    def getInterface(cls):
        '''Return instance of manager interface.'''
        cls._initialiseBridge()
        return ftrack_connect_nuke_studio.manager.ManagerInterface(cls._bridge)

    @classmethod
    def getUIDelegate(cls, interfaceInstance):
        '''Return instance of UI delegate.'''
        cls._initialiseBridge()

        # This import is here as certain ui modules should not be loaded
        # unless a ui delegate is requested.
        import ftrack_connect_nuke_studio.ui.delegate
        return ftrack_connect_nuke_studio.ui.delegate.Delegate(cls._bridge)
