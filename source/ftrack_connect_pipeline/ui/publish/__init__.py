# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack


def open(session):
    from . import dialog
    publish_dialog = dialog.Dialog(session)
    publish_dialog.exec_()
