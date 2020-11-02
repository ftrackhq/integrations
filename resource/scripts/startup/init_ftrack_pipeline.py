# file will be exec'd; there can be no encoding tag
# :copyright: Copyright (c) 2019 ftrack

import logging
import functools
import shiboken2
from Qt import QtWidgets

import ftrack_api

from ftrack_connect_pipeline_3dsmax import usage, host as max_host
from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline import constants

from pymxs import runtime as rt


logger = logging.getLogger('ftrack_connect_pipeline_3dsmax.scripts.userSetup')

created_dialogs = dict()

def _open_dialog(dialog_class, event_manager):
    '''Open *dialog_class* and create if not already existing.'''
    dialog_name = dialog_class

    if dialog_name not in created_dialogs:
        # https://help.autodesk.com/view/3DSMAX/2020/ENU/?guid=__developer_creating_python_uis_html
        main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
        main_window = shiboken2.wrapInstance(
            shiboken2.getCppPointer(main_window_qwdgt)[0],
            QtWidgets.QMainWindow
        )
        # TODO: mantain this to be able to create the dialog on versions < 2020
        #main_window = MaxPlus.GetQMaxMainWindow()
        ftrack_dialog = dialog_class
        created_dialogs[dialog_name] = ftrack_dialog(
            event_manager, parent=main_window
        )
    created_dialogs[dialog_name].show()

def initialise():

    logger.info('Setting up the menu')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=constants.LOCAL_EVENT_MODE
    )

    max_host.MaxHost(event_manager)

    usage.send_event(
        'USED-FTRACK-CONNECT-PIPELINE-3DS-MAX'
    )

    from ftrack_connect_pipeline_3dsmax.client import load
    from ftrack_connect_pipeline_3dsmax.client import publish
    from ftrack_connect_pipeline_3dsmax.client import asset_manager
    from ftrack_connect_pipeline_3dsmax.client import log_viewer

    # Enable loader and publisher only if is set to run local (default)
    dialogs = []

    dialogs.append(
        (load.MaxLoaderClient, 'Loader')
    )
    dialogs.append(
        (publish.MaxPublisherClient, 'Publisher')
    )
    dialogs.append(
        (asset_manager.MaxAssetManagerClient, 'AssetManager')
    )
    dialogs.append(
        (log_viewer.MaxLogViewerClient, 'LogViewer')
    )

    menu_name = 'ftrack_pipeline'

    if rt.menuMan.findMenu(menu_name):
        rt.menuMan.unRegisterMenu(menu_name)

    mainMenuBar = rt.menuMan.getMainMenuBar()
    ftrack_menu = rt.menuMan.createMenu(menu_name)

    # Register and hook the dialog in ftrack menu
    for item in dialogs:
        if item == 'divider':
            ftrack_menu.addItem(rt.menuMan.createSeparatorItem(), -1)
            continue

        dialog_class, label = item

        macro_name = "ftrack_menu_macro_{}".format(item)
        category = "ftrack"
        # The createActionItem expects a macro and not an script.
        rt.execute(
            """
            macroScript {macro_name}
            category: "{category}"
            (
                on execute do
                (
                    python.execute "{fxn}"
                )
            )
        """.format(
                macro_name=macro_name,
                category=category,
                fxn=functools.partial(
                    _open_dialog, dialog_class, event_manager
                )
            )
        )

        ftrack_menu.addItem(
            rt.menuMan.createActionItem(macro_name, category),
            -1
        )
    mainMenuBar.AddItem(ftrack_menu, -1)


initialise()
