# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import logging
import re
from ftrack_connect_pipeline_maya import usage, host as maya_host
from ftrack_connect_pipeline import event, host
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline_maya import constants

import maya.cmds as mc
import maya.mel as mm

logger = logging.getLogger('ftrack_connect_pipeline_maya.scripts.userSetup')

created_dialogs = dict()


def _open_dialog(dialog_class, hostid):
    '''Open *dialog_class* and create if not already existing.'''
    dialog_name = dialog_class

    if dialog_name not in created_dialogs:
        ftrack_dialog = dialog_class
        created_dialogs[dialog_name] = ftrack_dialog(
            hostid
        )

    created_dialogs[dialog_name].show()


def initialise():
    # TODO : later we need to bring back here all the maya initialiations from ftrack-connect-maya
    # such as frame start / end etc....
    session = get_shared_session()
    hostid = host.initialise(session, constants.HOST, constants.UI)

    usage.send_event(
        'USED-FTRACK-CONNECT-PIPELINE-MAYA'
    )

    mc.loadPlugin('ftrackMayaPlugin.py', quiet=True)

    if mc.about(win=True):
        match = re.match(
            '([0-9]{4}).*', mc.about(version=True)
        )

        if int(match.groups()[0]) >= 2018:
            import QtExt

            # Disable web widgets.
            QtExt.is_webwidget_supported = lambda: False

            logger.debug(
                'Disabling webwidgets due to maya 2018 '
                'QtWebEngineWidgets incompatibility.'
            )

    from ftrack_connect_pipeline_maya.client import load
    from ftrack_connect_pipeline_maya.client import publish

    # Enable loader and publisher only if is set to run local (default)
    remote_set = os.environ.get(
        'FTRACK_PIPELINE_REMOTE_EVENTS', False
    )
    dialogs = []

    if not remote_set:
        dialogs.append(
            (load.QtPipelineMayaLoaderWidget, 'Loader')
        )
        dialogs.append(
            (publish.QtPipelineMayaPublishWidget, 'Publisher')
        )

    else:
        maya_host.notify_connected_client(session, hostid)

    ftrack_menu = maya_host.get_ftrack_menu()
    # Register and hook the dialog in ftrack menu
    for item in dialogs:
        if item == 'divider':
            mc.menuItem(divider=True)
            continue

        dialog_class, label = item

        mc.menuItem(
            parent=ftrack_menu,
            label=label,
            command=(
                lambda x, dialog_class=dialog_class: _open_dialog(dialog_class, hostid)
            )
        )






mc.evalDeferred("initialise()", lp=True)
