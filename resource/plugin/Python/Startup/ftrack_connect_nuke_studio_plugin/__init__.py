# Import plugin to initiate it.
import ftrack_connect_nuke_studio.plugin
import ftrack_connect_nuke_studio.usage

# Send usage event.
ftrack_connect_nuke_studio.usage.send_event(
    'USED-FTRACK-CONNECT-NUKE-STUDIO'
)