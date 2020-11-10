# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


import logging
import functools
import shiboken2
from Qt import QtWidgets

from pymxs import runtime as rt

try:
    import MaxPlus
except ImportError:
    pass

created_dialogs = dict()

event_manager_storage = {}
dialog_class_storage = {}

class OpenDialog(object):

    def __init__(self):
        super(OpenDialog, self).__init__()

    def open_dialog(self, storage_id):
        '''Open *dialog_class* and create if not already existing.'''
        event_manager = event_manager_storage[storage_id]
        dialog_class = dialog_class_storage[storage_id]
        dialog_name = dialog_class

        if dialog_name not in created_dialogs:
            #This is working on 2020 but I hit the simbol error on getting the context twice
            # https://help.autodesk.com/view/3DSMAX/2020/ENU/?guid=__developer_creating_python_uis_html
            main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
            main_window = shiboken2.wrapInstance(
                shiboken2.getCppPointer(main_window_qwdgt)[0],
                QtWidgets.QMainWindow
            )
            # # TODO: mantain this to be able to create the dialog on versions < 2020
            # main_window = MaxPlus.GetQMaxMainWindow()
            ftrack_dialog = dialog_class
            created_dialogs[dialog_name] = ftrack_dialog(
                event_manager, parent=main_window
            )
        created_dialogs[dialog_name].show()
