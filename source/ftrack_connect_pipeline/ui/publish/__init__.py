# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

from . import dialog


def open(session):
    publish_dialog = dialog.Dialog(session)
    publish_dialog.exec_()
