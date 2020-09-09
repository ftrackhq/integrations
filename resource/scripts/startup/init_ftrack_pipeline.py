# file will be exec'd; there can be no encoding tag
# :copyright: Copyright (c) 2019 ftrack

import logging
import functools

import ftrack_api

from ftrack_connect_pipeline_3dsmax import usage, host as max_host
from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline import constants

import MaxPlus


logger = logging.getLogger('ftrack_connect_pipeline_3dsmax.scripts.userSetup')

created_dialogs = dict()


def _open_dialog(dialog_class, event_manager):
    '''Open *dialog_class* and create if not already existing.'''
    dialog_name = dialog_class

    if dialog_name not in created_dialogs:
        main_window = MaxPlus.GetQMaxMainWindow()
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

    if MaxPlus.MenuManager.MenuExists(menu_name):
        MaxPlus.MenuManager.UnregisterMenu(menu_name)

    ftrack_menu_builder = MaxPlus.MenuBuilder(menu_name)
    # Register and hook the dialog in ftrack menu
    for item in dialogs:
        if item == 'divider':
            ftrack_menu_builder.AddSeparator()
            continue

        dialog_class, label = item

        ftrack_menu_builder.AddItem(
            MaxPlus.ActionFactory.Create(
                category='ftrack',
                name=label,
                fxn=functools.partial(_open_dialog, dialog_class, event_manager)
            )
        )
    ftrack_menu_builder.Create(MaxPlus.MenuManager.GetMainMenu())


initialise()
