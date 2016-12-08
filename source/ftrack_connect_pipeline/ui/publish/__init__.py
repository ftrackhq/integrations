# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import ftrack_connect_pipeline.util


def open(session):
    '''Open publish dialog using *session*.'''
    from . import dialog
    publish_dialog = dialog.Dialog(
        ftrack_connect_pipeline.util.get_ftrack_entity(),
        session
    )
    publish_dialog.setMinimumSize(800, 600)
    publish_dialog.exec_()
