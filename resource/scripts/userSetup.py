# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import functools
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline_maya import host as maya_host

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


def get_ftrack_menu(menu_name='ftrack', submenu_name='pipeline'):
    '''Get the current ftrack menu, create it if does not exists.'''
    gMainWindow = mm.eval('$temp1=$gMainWindow')

    if cmds.menu(menu_name, exists=True, parent=gMainWindow, label=menu_name):
        menu = menu_name

    else:
        menu = cmds.menu(
            menu_name, parent=gMainWindow, tearOff=False, label=menu_name
        )

    if cmds.menuItem(
        submenu_name, exists=True, parent=menu, label=submenu_name
    ):
        submenu = submenu_name
    else:
        submenu = cmds.menuItem(
            submenu_name, subMenu=True, label=submenu_name, parent=menu
        )

    return submenu

def _open_widget(event_manager, widgets, event):
    '''Open Maya widget based on widget name in *event*, and create if not already
    exists'''
    widget_name = None
    for (_widget_name, widget_class, unused_label) in widgets:
        if _widget_name == event['data']['pipeline']['widget_name']:
            widget_name = _widget_name
            break
    if widget_name:
        if widget_name not in created_widgets:
            ftrack_client = widget_class
            created_widgets[widget_name] = ftrack_client(
                event_manager
            )
        created_widgets[widget_name].show()
    else:
        raise Exception('Unknown client {}!'.format(
            event['data']['pipeline']['widget_name'])
        )


def initialise():
    # TODO : later we need to bring back here all the maya initialisations
    #  from ftrack-connect-maya
    # such as frame start / end etc....

    logger.debug('Setting up the menu')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=constants.LOCAL_EVENT_MODE
    )

    host = maya_host.MayaHost(event_manager)

    cmds.loadPlugin('ftrackMayaPlugin.py', quiet=True)

    # Enable loader and publisher only if is set to run local (default)

    from ftrack_connect_pipeline_maya.client import open
    from ftrack_connect_pipeline_maya.client import load
    from ftrack_connect_pipeline_maya.client import publish
    from ftrack_connect_pipeline_maya.client import asset_manager
    from ftrack_connect_pipeline_maya.client import log_viewer

    widgets = list()
    widgets.append(
        (open.MayaOpenDialog, 'Open')
    )
    widgets.append(
        ('load', load.MayaLoaderClient, 'Loader')
    )
    widgets.append(
        ('publish', publish.MayaPublisherClient, 'Publisher')
    )
    widgets.append(
        ('asset_manager', asset_manager.MayaAssetManagerClient, 'Asset Manager')
    )
    widgets.append(
        ('log_viewer', log_viewer.MayaLogViewerClient, 'Log Viewer')
    )

    ftrack_menu = get_ftrack_menu()
    # Register and hook the dialog in ftrack menu
    for item in widgets:
        if item == 'divider':
            cmds.menuItem(divider=True)
            continue

        widget_name, unused_widget_class, label = item

        cmds.menuItem(
            parent=ftrack_menu,
            label=label,
            command=(functools.partial(host.launch_widget, widget_name)),
        )

    # Listen to client launch events
    session.event_hub.subscribe(
        'topic={} and data.pipeline.host_id={}'.format(
            qt_constants.PIPELINE_WIDGET_LAUNCH,
            host.host_id
        ),
        functools.partial(_open_widget, event_manager, widgets)
    )


cmds.evalDeferred('initialise()', lp=True)
