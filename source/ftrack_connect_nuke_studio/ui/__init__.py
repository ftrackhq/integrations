# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

# Load resources from ftrack-connect so that they can be used in this project.
import ftrack_connect.ui.resource

NUKE_STUDIO_OVERLAY_STYLE = '''
    BlockingOverlay {
        background-color: rgba(58, 58, 58, 200);
        border: none;
    }

    BlockingOverlay QFrame#content {
        padding: 0px;
        border: 80px solid transparent;
        background-color: transparent;
        border-image: none;
    }

    BlockingOverlay QLabel {
        background: transparent;
    }
'''
