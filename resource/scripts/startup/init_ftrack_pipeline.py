# file will be exec'd; there can be no encoding tag
# :copyright: Copyright (c) 2019 ftrack

import functools
import logging
import os
from qtpy import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline import host
from ftrack_connect_pipeline.session import get_shared_session
import MaxPlus

from ftrack_connect_pipeline_3dsmax import constants, usage, host as max_host


logger = logging.getLogger('ftrack_connect_pipeline_3dsmax.scripts.userSetup')

created_dialogs = dict()


def open_dialog(dialog_class, hostid):
    '''Open *dialog_class* and create if not already existing.'''
    dialog_name = dialog_class

    if dialog_name not in created_dialogs:
        main_window = MaxPlus.GetQMaxMainWindow()
        ftrack_dialog = dialog_class
        created_dialogs[dialog_name] = ftrack_dialog(
            hostid, parent=main_window
        )
    created_dialogs[dialog_name].show()


def load_and_init():
    session = get_shared_session()
    hostid = host.initialise(session, constants.HOST, constants.UI)

    usage.send_event(
        'USED-FTRACK-CONNECT-PIPELINE-3DS-MAX'
    )

    from ftrack_connect_pipeline_3dsmax.client import publish

    # Enable loader and publisher only if is set to run local (default)
    remote_set = os.environ.get(
        'FTRACK_PIPELINE_REMOTE_EVENTS', False
    )
    if not remote_set:
        dialogs = [
            (publish.QtPipelineMaxPublishWidget, 'Publisher'),
        ]
    else:
        max_host.notify_connected_client(session, hostid)

    menu_name = 'ftrack_pipeline'
    # ftrack_menu_builder = max_host.get_ftrack_menu()
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
                category='ftrack', name=label, fxn=functools.partial(
                    open_dialog, dialog_class, hostid
                )
            )
        )
    ftrack_menu_builder.Create(MaxPlus.MenuManager.GetMainMenu())


load_and_init()
