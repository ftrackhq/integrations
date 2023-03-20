# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import os
import tempfile
import logging
import functools

from Qt import QtWidgets, QtCore

import hou, hdefereval

import ftrack_api

from ftrack_connect_pipeline.configure_logging import configure_logging
from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.asset_manager.model import AssetListModel

from ftrack_connect_pipeline_houdini import host as houdini_host
from ftrack_connect_pipeline_houdini.client import (
    open as ftrack_open,
    load,
    asset_manager,
    publish,
    change_context,
    log_viewer,
    documentation,
)
from ftrack_connect_pipeline_houdini import utils as houdini_utils

configure_logging(
    'ftrack_connect_pipeline_houdini',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt'],
)

logger = logging.getLogger('ftrack_connect_pipeline_houdini')

event_manager = None
host = None
asset_list_model = None

# Define widgets and their classes
widgets = list()
widgets.append(
    (core_constants.OPENER, ftrack_open.HoudiniQtOpenerClientWidget, 'Open')
)
widgets.append(
    (
        qt_constants.ASSEMBLER_WIDGET,
        load.HoudiniQtAssemblerClientWidget,
        'Assembler',
    )
)
widgets.append(
    (
        core_constants.ASSET_MANAGER,
        asset_manager.HoudiniQtAssetManagerClientWidget,
        'Asset Manager',
    )
)
widgets.append(
    (
        core_constants.PUBLISHER,
        publish.HoudiniQtPublisherClientWidget,
        'Publisher',
    )
)
widgets.append(
    (
        qt_constants.CHANGE_CONTEXT_WIDGET,
        change_context.HoudiniQtChangeContextClientWidget,
        'Change context',
    )
)
widgets.append(
    (
        core_constants.LOG_VIEWER,
        log_viewer.HoudiniQtLogViewerClientWidget,
        'Log Viewer',
    )
)
widgets.append(
    (
        qt_constants.DOCUMENTATION_WIDGET,
        documentation.HoudiniQtDocumentationClientWidget,
        'Documentation',
    )
)

created_widgets = dict()


class EventFilterWidget(QtWidgets.QWidget):
    def eventFilter(self, obj, event):
        return False


def init():
    global event_manager, host, asset_list_model

    logger.debug('Setting up the menu')
    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=core_constants.LOCAL_EVENT_MODE
    )

    host = houdini_host.HoudiniHost(event_manager)

    # Shared asset manager model
    asset_list_model = AssetListModel(event_manager)

    # Listen to widget launch events
    session.event_hub.subscribe(
        'topic={} and data.pipeline.host_id={}'.format(
            core_constants.PIPELINE_CLIENT_LAUNCH, host.host_id
        ),
        functools.partial(_open_widget, event_manager, asset_list_model),
    )

    # Install dummy event filter to prevent Houdini from crashing during widget
    # build.
    QtCore.QCoreApplication.instance().installEventFilter(EventFilterWidget())

    try:
        houdini_utils.init_houdini()
    except Exception as error:
        # Continue execution if this fails
        logger.error(error)


def launchWidget(widget_name):
    '''Send an event to launch the widget'''
    host.launch_client(widget_name)


def _open_widget(event_manager, asset_list_model, event):
    '''Create and (re-)display a widget'''
    widget_name = None
    widget_class = None
    widget_label = None
    for _widget_name, _widget_class, _widget_label in widgets:
        if _widget_name == event['data']['pipeline']['name']:
            widget_name = _widget_name
            widget_class = _widget_class
            widget_label = _widget_label
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
                core_constants.PUBLISHER,
                core_constants.ASSET_MANAGER,
            ]:
                # Create a docked pypanel instance in Houdini interface
                pan_path = _generate_pypanel(widget_name, widget_label)
                hou.pypanel.installFile(pan_path)

                ftrack_id = 'Ftrack_ID'
                panel_interface = None

                try:
                    for interface, value in hou.pypanel.interfaces().items():
                        if interface == widget_label:
                            panel_interface = value
                            break
                except hou.OperationFailed as e:
                    logger.error(
                        'Something wrong with Python Panel: {}'.format(e)
                    )

                main_tab = hou.ui.curDesktop().findPaneTab(ftrack_id)
                if main_tab:
                    panel = main_tab.pane().createTab(
                        hou.paneTabType.PythonPanel
                    )
                    panel.showToolbar(False)
                    panel.setActiveInterface(panel_interface)
                else:
                    if panel_interface:
                        hou.hscript(
                            'pane -S -m pythonpanel -o -n {}'.format(ftrack_id)
                        )
                        panel = hou.ui.curDesktop().findPaneTab(ftrack_id)
                        panel.showToolbar(False)
                        panel.setActiveInterface(panel_interface)
            else:
                # Create and bring up a dialog
                if widget_name in [qt_constants.ASSEMBLER_WIDGET]:
                    # Create with asset model
                    widget = ftrack_client(event_manager, asset_list_model)
                else:
                    # Create without asset model
                    widget = ftrack_client(event_manager)
                created_widgets[widget_name] = widget
        if widget:
            widget.show()
            widget.raise_()
            widget.activateWindow()
    else:
        logger.warning(
            "Don't know how to open widget from event: {}".format(event)
        )


def _generate_pypanel(widget_name, panel_title):
    '''Write temporary xml file for pypanel'''
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<pythonPanelDocument>
  <interface name="{0}" label="{0}" icon="MISC_python" help_url="">
    <script><![CDATA[

import __main__

def createInterface():
    widget = __main__.pipelineWidgetFactory('{1}')
    __main__.created_widgets['{1}'] = widget
    return widget
]]></script>
    <help><![CDATA[]]></help>
  </interface>
</pythonPanelDocument>"""

    xml = xml.format(panel_title, widget_name)

    path = os.path.join(
        tempfile.gettempdir(),
        'ftrack',
        'connect',
        '{}.pypanel'.format(panel_title),
    )
    if os.path.exists(path):
        pass
    else:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        f = open(path, 'w')
        f.write(xml)
        f.close()
    return path


def pipelineWidgetFactory(widget_name):
    '''Instantiate the docked client panel widget'''
    if widget_name == core_constants.PUBLISHER:
        widget = publish.HoudiniQtPublisherClientWidget(event_manager)
    elif widget_name == core_constants.ASSET_MANAGER:
        widget = asset_manager.HoudiniQtAssetManagerClientWidget(
            event_manager, asset_list_model
        )
    created_widgets[widget_name] = widget
    return widget


hdefereval.executeDeferred(init)
