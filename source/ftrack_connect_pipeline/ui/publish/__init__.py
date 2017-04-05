# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack


def open(session, ftrack_entity):
    '''Open publish dialog using *session*.'''
    from . import dialog
    publish_dialog = dialog.Dialog(ftrack_entity, session)
    publish_dialog.setMinimumSize(800, 600)
    publish_dialog.exec_()
