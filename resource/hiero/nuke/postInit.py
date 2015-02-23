# This initializes the FnAssetAPI host
import foundry.assetmgr
import ftrack_connect_nuke_studio.plugin
# Select a locally available manager
nuke.assetmgr.start(ftrack_connect_nuke_studio.plugin.Plugin.getIdentifier())