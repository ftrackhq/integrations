# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import functools
import logging
import os

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
        ftrack_dialog = dialog_class
        created_dialogs[dialog_name] = ftrack_dialog(
            hostid
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

    ftrack_menu_builder = max_host.get_ftrack_menu()
    # Register and hook the dialog in ftrack menu
    for item in dialogs:
        if item == 'divider':
            ftrack_menu_builder.AddSeparator()
            continue

        dialog_class, label = item

        ftrack_menu_builder.addItem(
            MaxPlus.ActionFactory.Create(
                category='ftrack', name=label, fxn=functools.partial(
                    open_dialog, dialog_class, hostid
                )
            )
        )


load_and_init()
