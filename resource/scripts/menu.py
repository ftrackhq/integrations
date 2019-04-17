# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import logging

from ftrack_connect_pipeline_nuke import usage, host as nuke_host
from ftrack_connect_pipeline import event, host
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline_nuke import constants
import nuke

logger = logging.getLogger('ftrack_connect_pipeline_nuke.scripts.userSetup')

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


def initialise():
    # TODO : later we need to bring back here all the nuke initialiations from ftrack-connect-nuke
    # such as frame start / end etc....
    session = get_shared_session()
    hostid = host.initialise(session, constants.HOST, constants.UI)

    usage.send_event(
        'USED-FTRACK-CONNECT-PIPELINE-NUKE'
    )

    from ftrack_connect_pipeline_nuke.client import load
    from ftrack_connect_pipeline_nuke.client import publish

    # Enable loader and publisher only if is set to run local (default)
    remote_set = os.environ.get(
        'FTRACK_PIPELINE_REMOTE_EVENTS', False
    )
    dialogs = []

    if not remote_set:
        dialogs.append(
            (load.QtPipelineNukeLoaderWidget, 'Loader')
        )
        dialogs.append(
            (publish.QtPipelineNukePublishWidget, 'Publisher')
        )

    else:
        nuke_host.notify_connected_client(session, hostid)

    ftrack_menu = nuke_host.get_ftrack_menu()

    for item in dialogs:
        if item == 'divider':
            ftrack_menu.addSeparator()
            continue

        dialog_class, label = item

        ftrack_menu.addCommand(label, lambda dialog_class=dialog_class: open_dialog(dialog_class, hostid))






initialise()
