# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import functools
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline_maya import host as maya_host
from ftrack_connect_pipeline_qt.utils import BaseThread
import time

import maya.utils
import maya.cmds as cmds
import maya.mel as mm

import ftrack_api

from ftrack_connect_pipeline.configure_logging import configure_logging

extra_handlers = {
    'maya': {
        'class': 'maya.utils.MayaGuiLogHandler',
        'level': 'INFO',
        'formatter': 'file',
    }
}
configure_logging(
    'ftrack_connect_pipeline_maya',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt'],
    extra_handlers=extra_handlers,
    propagate=False,
)


logger = logging.getLogger('ftrack_connect_pipeline_maya')


created_widgets = dict()


def get_ftrack_menu(menu_name='ftrack', submenu_name=None):
    '''Get the current ftrack menu, create it if does not exists.'''
    gMainWindow = mm.eval('$temp1=$gMainWindow')

    if cmds.menu(menu_name, exists=True, parent=gMainWindow, label=menu_name):
        menu = menu_name

    else:
        menu = cmds.menu(
            menu_name, parent=gMainWindow, tearOff=True, label=menu_name
        )

    if submenu_name:
        if cmds.menuItem(
            submenu_name, exists=True, parent=menu, label=submenu_name
        ):
            submenu = submenu_name
        else:
            submenu = cmds.menuItem(
                submenu_name, subMenu=True, label=submenu_name, parent=menu
            )
        return submenu
    else:
        return menu


def _open_widget(event_manager, asset_list_model, widgets, event):
    '''Open Maya widget based on widget name in *event*, and create if not already
    exists'''
    widget_name = None
    widget_class = None
    for (_widget_name, _widget_class, unused_label, unused_image) in widgets:
        if _widget_name == event['data']['pipeline']['widget_name']:
            widget_name = _widget_name
            widget_class = _widget_class
            break
    if widget_name:
        if widget_name not in created_widgets:
            ftrack_client = widget_class
            created_widgets[widget_name] = ftrack_client(
                event_manager, asset_list_model
            )
        created_widgets[widget_name].show()
    else:
        raise Exception(
            'Unknown widget {}!'.format(
                event['data']['pipeline']['widget_name']
            )
        )


host = None


def initialise():
    # TODO : later we need to bring back here all the maya initialisations
    #  from ftrack-connect-maya
    # such as frame start / end etc....

    global host

    logger.debug('Setting up the menu')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=constants.LOCAL_EVENT_MODE
    )

    host = maya_host.MayaHost(event_manager)

    cmds.loadPlugin('ftrackMayaPlugin.py', quiet=True)

    from ftrack_connect_pipeline_qt.ui.asset_manager.base import AssetListModel
    from ftrack_connect_pipeline_qt import constants as qt_constants

    # Shared asset manager model
    asset_list_model = AssetListModel(event_manager)

    from ftrack_connect_pipeline_maya.client import open
    from ftrack_connect_pipeline_maya.client import assembler
    from ftrack_connect_pipeline_maya.client import save
    from ftrack_connect_pipeline_maya.client import asset_manager
    from ftrack_connect_pipeline_maya.client import publish
    from ftrack_connect_pipeline_maya.client import log_viewer
    from ftrack_connect_pipeline_qt import client

    widgets = list()
    widgets.append(
        (qt_constants.OPEN_WIDGET, open.MayaOpenDialog, 'Open', 'fileOpen')
    )
    widgets.append(
        (
            qt_constants.ASSEMBLER_WIDGET,
            assembler.MayaAssemblerDialog,
            'Assembler',
            'greasePencilImport',
        )
    )
    widgets.append(
        (
            qt_constants.ASSET_MANAGER_WIDGET,
            asset_manager.MayaAssetManagerClient,
            'Asset Manager',
            'volumeCube',
        )
    )
    widgets.append(
        (
            qt_constants.SAVE_WIDGET,
            save.QtSaveClient,
            'Save Snapshot',
            'fileSave',
        )
    )
    widgets.append(
        (
            qt_constants.PUBLISHER_WIDGET,
            publish.MayaPublisherClient,
            'Publisher',
            'greasePencilExport',
        )
    )
    widgets.append(
        (
            qt_constants.LOG_VIEWER_WIDGET,
            log_viewer.MayaLogViewerDialog,
            'Log Viewer',
            'zoom',
        )
    )
    widgets.append(
        (
            qt_constants.DOC_WIDGET,
            client.QtDocumentationClient,
            'Documentation',
            'SP_FileIcon',
        )
    )

    ftrack_menu = get_ftrack_menu()
    # Register and hook the dialog in ftrack menu
    for item in widgets:
        if item == 'divider':
            cmds.menuItem(divider=True)
            continue

        widget_name, unused_widget_class, label, image = item

        cmds.menuItem(
            parent=ftrack_menu,
            label=label,
            command=(functools.partial(host.launch_widget, widget_name)),
            image=":/{}.png".format(image),
        )

    # Listen to client launch events
    session.event_hub.subscribe(
        'topic={} and data.pipeline.host_id={}'.format(
            constants.PIPELINE_WIDGET_LAUNCH, host.host_id
        ),
        functools.partial(
            _open_widget, event_manager, asset_list_model, widgets
        ),
    )

    # host.launch_widget(qt_constants.OPEN_WIDGET)


cmds.evalDeferred('initialise()', lp=True)
