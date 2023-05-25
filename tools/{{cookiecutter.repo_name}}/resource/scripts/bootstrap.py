# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

# Example DCC bootstrap script based on Maya userSetup.py

import logging
import functools

# import maya.cmds as cmds
# import maya.mel as mm

import ftrack_api

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.configure_logging import configure_logging

from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.asset_manager.model import AssetListModel

from {{cookiecutter.package_name}} import host as {{cookiecutter.host_type}}_host
from {{cookiecutter.package_name}}.client import (
    open as ftrack_open,
    load,
    asset_manager,
    publish,
    change_context,
    log_viewer,
    documentation
)

from {{cookiecutter.package_name}} import utils as {{cookiecutter.host_type}}_utils


extra_handlers = {
    '{{cookiecutter.host_type}}': {
        'class': '{{cookiecutter.host_type}}.utils.{{cookiecutter.host_type_capitalized}}GuiLogHandler',
        'level': 'INFO',
        'formatter': 'file',
    }
}
configure_logging(
    '{{cookiecutter.package_name}}',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt'],
    extra_handlers=extra_handlers,
    propagate=False,
)


logger = logging.getLogger('{{cookiecutter.package_name}}')


created_widgets = dict()


def get_ftrack_menu(menu_name='ftrack', submenu_name=None):
    '''Get the current ftrack menu, create it if does not exists.'''
    # gMainWindow = mm.eval('$temp1=$gMainWindow')
    #
    # if cmds.menu(menu_name, exists=True, parent=gMainWindow, label=menu_name):
    #     menu = menu_name
    #
    # else:
    #     menu = cmds.menu(
    #         menu_name, parent=gMainWindow, tearOff=True, label=menu_name
    #     )

    if submenu_name:
        # if cmds.menuItem(
        #     submenu_name, exists=True, parent=menu, label=submenu_name
        # ):
        #     submenu = submenu_name
        # else:
        #     submenu = cmds.menuItem(
        #         submenu_name, subMenu=True, label=submenu_name, parent=menu
        #     )
        return submenu
    else:
        return menu


def _open_widget(event_manager, asset_list_model, widgets, event):
    '''Open {{cookiecutter.host_type_capitalized}} widget based on widget name in *event*, and create if not already
    exists'''
    widget_name = None
    widget_class = None
    for (_widget_name, _widget_class, unused_label, unused_image) in widgets:
        if _widget_name == event['data']['pipeline']['name']:
            widget_name = _widget_name
            widget_class = _widget_class
            break
    if widget_name:
        ftrack_client = widget_class
        widget = None
        if widget_name in created_widgets:
            widget = created_widgets[widget_name]
            # Is it still visible?
            is_valid_and_visible = False
            try:
                if widget is not None and widget.isVisible():
                    is_valid_and_visible = True
            except:
                pass
            finally:
                if not is_valid_and_visible:
                    del created_widgets[widget_name]  # Not active any more
                    if widget:
                        try:
                            widget.deleteLater()  # Make sure it is deleted
                        except:
                            pass
                        widget = None
        if widget is None:
            # Need to create
            if widget_name in [
                qt_constants.ASSEMBLER_WIDGET,
                core_constants.ASSET_MANAGER,
            ]:
                # Create with asset model
                widget = ftrack_client(event_manager, asset_list_model)
            else:
                # Create without asset model
                widget = ftrack_client(event_manager)
            created_widgets[widget_name] = widget
        widget.show()
        widget.raise_()
        widget.activateWindow()
    else:
        raise Exception(
            'Unknown widget {}!'.format(event['data']['pipeline']['name'])
        )


def initialise():
    # TODO : later we need to bring back here all the {{cookiecutter.host_type}} initialisations
    #  from ftrack-connect-{{cookiecutter.host_type}}
    # such as frame start / end etc....

    logger.debug('Setting up the menu')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=core_constants.LOCAL_EVENT_MODE
    )

    host = {{cookiecutter.host_type}}_host.{{cookiecutter.host_type_capitalized}}Host(event_manager)

    cmds.loadPlugin('ftrack{{cookiecutter.host_type_capitalized}}Plugin.py', quiet=True)

    # Shared asset manager model
    asset_list_model = AssetListModel(event_manager)

    widgets = list()
    widgets.append(
        (
            core_constants.OPENER,
            ftrack_open.{{cookiecutter.host_type_capitalized}}QtOpenerClientWidget,
            'Open',
            'fileOpen',
        )
    )
    widgets.append(
        (
            qt_constants.ASSEMBLER_WIDGET,
            load.{{cookiecutter.host_type_capitalized}}QtAssemblerClientWidget,
            'Assembler',
            'greasePencilImport',
        )
    )
    widgets.append(
        (
            core_constants.ASSET_MANAGER,
            asset_manager.{{cookiecutter.host_type_capitalized}}QtAssetManagerClientWidgetMixin,
            'Asset Manager',
            'volumeCube',
        )
    )
    widgets.append(
        (
            core_constants.PUBLISHER,
            publish.{{cookiecutter.host_type_capitalized}}QtPublisherClientWidgetMixin,
            'Publisher',
            'greasePencilExport',
        )
    )
    widgets.append(
        (
            qt_constants.CHANGE_CONTEXT_WIDGET,
            change_context.{{cookiecutter.host_type_capitalized}}QtChangeContextClientWidget,
            'Change context',
            'refresh',
        )
    )
    widgets.append(
        (
            core_constants.LOG_VIEWER,
            log_viewer.{{cookiecutter.host_type_capitalized}}QtLogViewerClientWidget,
            'Log Viewer',
            'zoom',
        )
    )
    widgets.append(
        (
            qt_constants.DOCUMENTATION_WIDGET,
            documentation.QtDocumentationClientWidget,
            'Documentation',
            'SP_FileIcon',
        )
    )

    ftrack_menu = get_ftrack_menu()
    # Register and hook the dialog in ftrack menu
    for item in widgets:
        # if item == 'divider':
        #     cmds.menuItem(divider=True)
        #     continue
        #
        # widget_name, unused_widget_class, label, image = item
        #
        # cmds.menuItem(
        #     parent=ftrack_menu,
        #     label=label,
        #     command=(functools.partial(host.launch_client, widget_name)),
        #     image=":/{}.png".format(image),
        # )

    # Listen to widget launch events
    session.event_hub.subscribe(
        'topic={} and data.pipeline.host_id={}'.format(
            core_constants.PIPELINE_CLIENT_LAUNCH, host.host_id
        ),
        functools.partial(
            _open_widget, event_manager, asset_list_model, widgets
        ),
    )

    {{cookiecutter.host_type}}_utils.init_{{cookiecutter.host_type}}()

    # host.launch_client(qt_constants.OPENER_WIDGET)


# cmds.evalDeferred('initialise()', lp=True)
