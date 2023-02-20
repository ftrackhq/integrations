# file will be exec'd; there can be no encoding tag
# :copyright: Copyright (c) 2014-2022 ftrack
import logging

from functools import partial

from pymxs import runtime as rt

from Qt import QtCore, QtWidgets

import ftrack_api

from ftrack_connect_pipeline_3dsmax import host as max_host
from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline import constants

from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline.configure_logging import configure_logging

from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.asset_manager.model import AssetListModel
from ftrack_connect_pipeline_qt.client import documentation

from ftrack_connect_pipeline_3dsmax import menu as ftrack_menu_module
from ftrack_connect_pipeline_3dsmax.client import (
    open,
    load,
    publish,
    asset_manager,
    log_viewer,
    change_context,
)
from ftrack_connect_pipeline_3dsmax.utils import custom_commands as max_utils

configure_logging(
    'ftrack_connect_pipeline_3dsmax',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt'],
)

logger = logging.getLogger('ftrack_connect_pipeline_3dsmax')

created_widgets = dict()


def _open_widget(event_manager, asset_list_model, widgets, event):
    '''Open 3D Studio Max widget based on widget name in *event*, and create if not already
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
            if widget_name in [
                qt_constants.ASSEMBLER_WIDGET,
                core_constants.ASSET_MANAGER,
            ]:
                widget = ftrack_client(
                    event_manager,
                    asset_list_model,
                    parent=max_utils.get_main_window(),
                )
            else:
                widget = ftrack_client(
                    event_manager, parent=max_utils.get_main_window()
                )

            created_widgets[widget_name] = widget
        widget.show()
        widget.raise_()
        widget.activateWindow()
    else:
        raise Exception(
            'Unknown widget {}!'.format(event['data']['pipeline']['name'])
        )


class EventFilterWidget(QtWidgets.QWidget):
    def eventFilter(self, obj, event):
        return False


def initialise():

    logger.debug('Setting up the menu')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=constants.LOCAL_EVENT_MODE
    )

    host = max_host.MaxHost(event_manager)

    ftrack_menu_module.host = host

    asset_list_model = AssetListModel(event_manager)

    # Enable loader and publisher only if is set to run local (default)

    widgets = list()

    widgets.append(
        (
            core_constants.OPENER,
            open.MaxQtOpenerClientWidget,
            'Open',
            '',
        )
    )
    widgets.append(
        (
            qt_constants.ASSEMBLER_WIDGET,
            load.MaxQtAssemblerClientWidget,
            'Assembler',
            '',
        )
    )
    widgets.append(
        (
            core_constants.ASSET_MANAGER,
            asset_manager.MaxQtAssetManagerClientWidget,
            'Asset Manager',
            '',
        )
    )
    widgets.append(
        (
            core_constants.PUBLISHER,
            publish.MaxQtPublisherClientWidget,
            'Publisher',
            '',
        )
    )
    widgets.append(
        (
            qt_constants.CHANGE_CONTEXT_WIDGET,
            change_context.MaxQtChangeContextClientWidget,
            'Change context',
            '',
        )
    )
    widgets.append(
        (
            core_constants.LOG_VIEWER,
            log_viewer.MaxQtLogViewerClientWidget,
            'Log Viewer',
            '',
        )
    )
    widgets.append(
        (
            qt_constants.DOCUMENTATION_WIDGET,
            documentation.QtDocumentationClientWidget,
            'Documentation',
            '',
        )
    )

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

        widget_name, dialog_class, label, unused_icon_name = item

        macro_name = widget_name
        category = "ftrack"

        # The createActionItem expects a macro and not an script.
        python_code = ";".join(
            [
                "from ftrack_connect_pipeline_3dsmax.menu import LaunchDialog",
                "launch_dialog_class = LaunchDialog()",
                "launch_dialog_class.launch_dialog('{}')".format(widget_name),
            ]
        )
        MAXSCRIPT = 'python.execute "{}"'.format(python_code)
        rt.macros.new(
            category,
            macro_name,
            "Launch ftrack {}".format(label),
            label,
            MAXSCRIPT,
        )

        ftrack_menu.addItem(
            rt.menuMan.createActionItem(macro_name, category), -1
        )
        i += 1

    sub_menu_ftrack_item = rt.menuMan.createSubMenuItem(menu_name, ftrack_menu)
    sub_menu_ftrack_index = main_menu_bar.numItems() - 1
    main_menu_bar.addItem(sub_menu_ftrack_item, sub_menu_ftrack_index)

    rt.menuMan.updateMenuBar()

    # Listen to widget launch events
    session.event_hub.subscribe(
        'topic={} and data.pipeline.host_id={}'.format(
            core_constants.PIPELINE_CLIENT_LAUNCH, host.host_id
        ),
        partial(
            _open_widget,
            event_manager,
            asset_list_model,
            widgets,
        ),
    )

    # Install dummy event filter to prevent Houdini from crashing during widget
    # build.
    QtCore.QCoreApplication.instance().installEventFilter(EventFilterWidget())

    max_utils.init_max()


initialise()
