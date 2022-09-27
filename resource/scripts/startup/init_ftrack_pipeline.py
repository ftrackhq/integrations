# file will be exec'd; there can be no encoding tag
# :copyright: Copyright (c) 2019-2022 ftrack

import uuid
import logging
import shiboken2
import functools

from Qt import QtWidgets

from pymxs import runtime as rt

import ftrack_api

from ftrack_connect_pipeline_3dsmax import host as max_host
from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.configure_logging import configure_logging

from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.asset_manager.model import AssetListModel

from ftrack_connect_pipeline_3dsmax.client import (
    open as ftrack_open,
    load,
    asset_manager,
    publish,
    change_context,
    log_viewer,
)
from ftrack_connect_pipeline_qt.client import documentation

configure_logging(
    'ftrack_connect_pipeline_3dsmax',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt']
)

logger = logging.getLogger('ftrack_connect_pipeline_3dsmax')

created_widgets = dict()

def _open_widget(event_manager, asset_list_model, widgets, event):
    '''Open Max widget based on widget name in *event*, and create if not already
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
            parent = None
            if widget_name in [core_constants.PUBLISHER, core_constants.ASSET_MANAGER]:
                #  Widget will be docked
                main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
                parent = shiboken2.wrapInstance(
                    shiboken2.getCppPointer(main_window_qwdgt)[0],
                    QtWidgets.QMainWindow
                )
            if widget_name in [
                qt_constants.ASSEMBLER_WIDGET,
                core_constants.ASSET_MANAGER,
            ]:
                # Create with asset model
                widget = ftrack_client(event_manager, asset_list_model, parent=parent)
            else:
                # Create without asset model
                widget = ftrack_client(event_manager, parent=parent)
            created_widgets[widget_name] = widget

        widget.show()
        widget.raise_()
        widget.activateWindow()
    else:
        raise Exception(
            'Unknown widget {}!'.format(event['data']['pipeline']['name'])
        )

def initialise():

    logger.debug('Setting up the menu')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=core_constants.LOCAL_EVENT_MODE
    )
    
    host = max_host.MaxHost(event_manager)

    # Shared asset manager model
    asset_list_model = AssetListModel(event_manager)

    # Enable loader and publisher only if is set to run local (default)
    widgets = list()
    widgets.append(
        (
            core_constants.OPENER,
            ftrack_open.MaxQtOpenerClientWidget,
            'Open',
            'fileOpen',
        )
    )
    widgets.append(
        (
            qt_constants.ASSEMBLER_WIDGET,
            load.MaxQtAssemblerClientWidget,
            'Assembler',
            'greasePencilImport',
        )
    )
    widgets.append(
        (
            core_constants.ASSET_MANAGER,
            asset_manager.MaxQtAssetManagerClientWidgetMixin,
            'Asset Manager',
            'volumeCube',
        )
    )
    widgets.append(
        (
            core_constants.PUBLISHER,
            publish.MaxQtPublisherClientWidgetMixin,
            'Publisher',
            'greasePencilExport',
        )
    )
    widgets.append(
        (
            qt_constants.CHANGE_CONTEXT_WIDGET,
            change_context.MaxQtChangeContextClientWidget,
            'Change context',
            'refresh',
        )
    )
    widgets.append(
        (
            core_constants.LOG_VIEWER,
            log_viewer.MaxQtLogViewerClientWidget,
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

    # Build menu
    menu_name = 'ftrack'

    if rt.menuMan.findMenu(menu_name):
        menu = rt.menuMan.findMenu(menu_name)
        rt.menuMan.unRegisterMenu(menu)

    main_menu_bar = rt.menuMan.getMainMenuBar()
    ftrack_menu = rt.menuMan.createMenu(menu_name)

    # Register and hook the dialog in ftrack menu
    i = 0
    for item in widgets:
        if item == 'divider':
            ftrack_menu.addItem(rt.menuMan.createSeparatorItem(), -1)
            continue

        widget_name, dialog_class, label, unused_icon = item

        #storage_id = str(uuid.uuid4())
        #ftrack_menu_module.event_manager_storage[storage_id] = event_manager
        #ftrack_menu_module.dialog_class_storage[storage_id] = dialog_class

        macro_name = label
        category = "ftrack"

        # The createActionItem expects a macro and not an script.
        python_code = "\n".join(
            [
                "host.launch_client('{}')".format(widget_name),
            ]
        )
        rt.execute(
            """
            macroScript {macro_name}
            category: "{category}"
            (
                on execute do
                (
                    python.execute "{p_code}"
                )
            )
        """.format(
                macro_name=macro_name,
                category=category,
                p_code=python_code
            )
        )

        ftrack_menu.addItem(
            rt.menuMan.createActionItem(macro_name, category),
            -1
        )
        i += 1

    sub_menu_pipeline_item = rt.menuMan.createSubMenuItem(
        submenu_name, pipeline_menu
    )
    sub_menu_pipeline_index = ftrack_menu.numItems() - 1
    ftrack_menu.addItem(sub_menu_pipeline_item, sub_menu_pipeline_index)

    sub_menu_ftrack_item = rt.menuMan.createSubMenuItem(menu_name, ftrack_menu)
    sub_menu_ftrack_index = main_menu_bar.numItems() - 1
    main_menu_bar.addItem(sub_menu_ftrack_item, sub_menu_ftrack_index)

    rt.menuMan.updateMenuBar()

    # Listen to widget launch events
    session.event_hub.subscribe(
        'topic={} and data.pipeline.host_id={}'.format(
            core_constants.PIPELINE_CLIENT_LAUNCH, host.host_id
        ),
        functools.partial(
            _open_widget, event_manager, asset_list_model, widgets
        ),
    )



initialise()
