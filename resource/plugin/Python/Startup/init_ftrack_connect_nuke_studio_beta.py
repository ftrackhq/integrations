# Import plugin to initiate it.
import ftrack_connect_nuke_studio_beta.plugin
import ftrack_connect_nuke_studio_beta.usage

# Send usage event.
ftrack_connect_nuke_studio_beta.usage.send_event(
    'USED-FTRACK-CONNECT-NUKE-STUDIO-BETA'
)