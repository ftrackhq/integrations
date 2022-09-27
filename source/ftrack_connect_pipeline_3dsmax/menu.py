# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets

try:
    # https://help.autodesk.com/view/3DSMAX/2020/ENU/?guid=__developer_creating_python_uis_html
    #This works for max >= 2020
    import shiboken2
    MAX_MIN_VERSION = '2020'
except ImportError:
    # MaxPlus is the recommended way to use in max <= 2019 even that we could
    # use the following: from PySide2 import shiboken2 #but seems to be slower.
    # https://help.autodesk.com/view/3DSMAX/2019/ENU/?guid=__developer_using_pyside_html
    # This works for max <= 2020
    import MaxPlus
    MAX_MIN_VERSION = '2019'

from pymxs import runtime as rt

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
            if MAX_MIN_VERSION == '2020':
                main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
                main_window = shiboken2.wrapInstance(
                    shiboken2.getCppPointer(main_window_qwdgt)[0],
                    QtWidgets.QMainWindow
                )
            else:
                main_window = MaxPlus.GetQMaxMainWindow()
            ftrack_dialog = dialog_class
            created_dialogs[dialog_name] = ftrack_dialog(
                event_manager, parent=main_window
            )
        created_dialogs[dialog_name].show()
