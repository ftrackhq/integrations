# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

from ftrack_connect_pipeline.ui import resource


OVERLAY_DARK_STYLE = '''
    BlockingOverlay  {
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

    PublishResult  {
        background-color: rgba(58, 58, 58, 200);
        border: none;
    }

    PublishResult QFrame#content {
        padding: 0px;
        border: 80px solid transparent;
        background-color: rgba(58, 58, 58, 200);
        border-image: none;
    }

    PublishResult QLabel {
        background: transparent;
    }
'''