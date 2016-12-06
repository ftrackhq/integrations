# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack


def open(session):
    '''Open publish dialog using *session*.'''
    from . import dialog
    publish_dialog = dialog.Dialog(session)
    publish_dialog.setMinimumSize(800, 600)
    publish_dialog.exec_()
