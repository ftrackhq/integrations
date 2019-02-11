# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


import logging
import threading
import re
from ftrack_connect_pipeline import host
from ftrack_connect_pipeline_maya import usage
import ftrack_connect_pipeline_maya #  import to configure logging

import maya.cmds as mc
import maya.mel as mm

logger = logging.getLogger('ftrack_connect_pipeline_maya.scripts.userSetup')

created_dialogs = dict()


def open_dialog(dialog_class):
    '''Open *dialog_class* and create if not already existing.'''
    dialog_name = dialog_class

    if dialog_name not in created_dialogs:
        ftrack_dialog = dialog_class
        created_dialogs[dialog_name] = ftrack_dialog()

    created_dialogs[dialog_name].show()


def get_ftrack_menu(menu_name = 'ftrack-pipeline'):
    gMainWindow = mm.eval('$temp1=$gMainWindow')

    if mc.menu(menu_name, exists=True):
        menu = menu_name

    else:
        menu = mc.menu(
            menu_name,
            parent=gMainWindow,
            tearOff=False,
            label=menu_name
        )

    return menu


def load_and_init():
    # TODO : later we need to bring back here all the maya initialiations from ftrack-connect-maya
    # such as frame start / end etc....

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

    from ftrack_connect_pipeline_maya.qt import load
    from ftrack_connect_pipeline_maya.qt import publish

    dialogs = [
        (load.QtPipelineMayaLoaderWidget, 'Loader'),
        (publish.QtPipelineMayaPublishWidget, 'Publisher')
    ]

    ftrack_menu = get_ftrack_menu()
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
                lambda x, dialog_class=dialog_class: open_dialog(dialog_class)
            )
        )


def register_hub_host():
    t = threading.Thread(target=host.start_host_listener)
    t.daemon = True
    t.start()
    logger.info('thread started!')


mc.evalDeferred("register_hub_host()", lp=True)
mc.evalDeferred("load_and_init()", lp=True)
