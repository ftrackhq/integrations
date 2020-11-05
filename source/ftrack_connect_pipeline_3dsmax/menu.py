# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


import logging
import functools
import shiboken2
from Qt import QtWidgets

import MaxPlus
from pymxs import runtime as rt

created_dialogs = dict()

import imp
import os


# def load_class(full_class_string):
#     """
#     Dynamically load a class from a string
#
#     #>>> klass = load_class("module.submodule.ClassName")
#     #>>> klass2 = load_class("myfile.Class2")
#     """
#     class_data = full_class_string.split(".")
#
#     module_str = class_data[0]
#     class_str = class_data[-1]
#     submodules_list = []
#
#     if len(class_data) > 2:
#         submodules_list = class_data[1:-1]
#
#     f, filename, description = imp.find_module(module_str)
#     module = imp.load_module(module_str, f, filename, description)
#
#     # Find each submodule
#     for smod in submodules_list:
#         path = os.path.dirname(filename) if os.path.isfile(
#             filename) else filename
#
#         f, filename, description = imp.find_module(smod, [path])
#
#         # Now we can load the module
#         try:
#             module = imp.load_module(" ".join(class_data[:-1]), f, filename,
#                                      description)
#         finally:
#             if f:
#                 f.close()
#
#     # Finally, we retrieve the Class
#     return getattr(module, class_str)
#
# def open_dialog(dialog_class, event_manager):
#     '''Open *dialog_class* and create if not already existing.'''
#     dialog_class = load_class(dialog_class)
#     event_manager = load_class(event_manager)
#     dialog_name = dialog_class
#
#     if dialog_name not in created_dialogs:
#         # https://help.autodesk.com/view/3DSMAX/2020/ENU/?guid=__developer_creating_python_uis_html
#         # main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
#         # main_window = shiboken2.wrapInstance(
#         #     shiboken2.getCppPointer(main_window_qwdgt)[0],
#         #     QtWidgets.QMainWindow
#         # )
#         # TODO: mantain this to be able to create the dialog on versions < 2020
#         main_window = MaxPlus.GetQMaxMainWindow()
#         ftrack_dialog = dialog_class
#         created_dialogs[dialog_name] = ftrack_dialog(
#             event_manager, parent=main_window
#         )
#     created_dialogs[dialog_name].show()

class OpenDialog(object):
    event_manager_storage = {}
    dialog_class_storage = {}

    def __init__(self):
        super(OpenDialog, self).__init__()

    def open_dialog(self, storage_id):
        '''Open *dialog_class* and create if not already existing.'''
        event_manager = self.event_manager_storage[storage_id]
        dialog_class = self.dialog_class_storage[storage_id]
        dialog_name = dialog_class

        if dialog_name not in created_dialogs:
            # https://help.autodesk.com/view/3DSMAX/2020/ENU/?guid=__developer_creating_python_uis_html
            # main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
            # main_window = shiboken2.wrapInstance(
            #     shiboken2.getCppPointer(main_window_qwdgt)[0],
            #     QtWidgets.QMainWindow
            # )
            # TODO: mantain this to be able to create the dialog on versions < 2020
            main_window = MaxPlus.GetQMaxMainWindow()
            ftrack_dialog = dialog_class
            created_dialogs[dialog_name] = ftrack_dialog(
                event_manager, parent=main_window
            )
        created_dialogs[dialog_name].show()
