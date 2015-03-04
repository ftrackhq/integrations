# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

# This initializes the FnAssetAPI host
import nuke.assetmgr
import ftrack_connect_nuke_studio.plugin
# Select a locally available manager
nuke.assetmgr.start(ftrack_connect_nuke_studio.plugin.Plugin.getIdentifier())