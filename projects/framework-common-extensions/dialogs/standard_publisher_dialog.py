# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

import ftrack_constants as constants
from ftrack_utils.framework.config.tool import get_plugins, get_groups
from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_qt.widgets.accordion import AccordionBaseWidget
from ftrack_qt.widgets.progress import ProgressWidget
from ftrack_qt.utils.widget import build_progress_data
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class StandardPublisherDialog(BaseContextDialog):
    '''Default Framework Publisher dialog'''

    name = 'framework_standard_publisher_dialog'
    tool_config_type_filter = ['publisher']
    ui_type = 'qt'
    run_button_title = 'PUBLISH'
    docked = True

    def __init__(
        self,
        event_manager,
        client_id,
        connect_methods_callback,
        connect_setter_property_callback,
        connect_getter_property_callback,
        tool_config_names,
        dialog_options,
        parent=None,
    ):
        '''
        Initialize Mixin class publisher dialog. It will load the qt dialog and
        mix it with the framework dialog.
        *event_manager*: instance of
        :class:`~ftrack_framework_core.event.EventManager`
        *client_id*: Id of the client that initializes the current dialog
        *connect_methods_callback*: Client callback method for the dialog to be
        able to execute client methods.
        *connect_setter_property_callback*: Client callback property setter for
        the dialog to be able to read client properties.
        *connect_getter_property_callback*: Client callback property getter for
        the dialog to be able to write client properties.
        *tool_config_names*: List of tool config names passed on to configure the
        current dialog.
        *dialog_options*: Dictionary of arguments passed on to configure the
        current dialog.
        '''
        self._scroll_area = None
        self._scroll_area_widget = None
        self._progress_widget = None

        super(StandardPublisherDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            tool_config_names,
            dialog_options,
            parent=parent,
        )

    def pre_build_ui(self):
        # Create scroll area to add all the widgets
        self._scroll_area = QtWidgets.QScrollArea()
        self._scroll_area.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )

        # Create a main widget for the scroll area
        self._scroll_area_widget = QtWidgets.QWidget()
        scroll_area_widget_layout = QtWidgets.QVBoxLayout()
        scroll_area_widget_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll_area_widget.setLayout(scroll_area_widget_layout)

        self.tool_widget.layout().addWidget(self._scroll_area, 100)
        self._scroll_area.setWidget(self._scroll_area_widget)

    def build_ui(self):
        # Select the desired tool_config

        self.tool_config = None
        tool_config_message = None
        if self.filtered_tool_configs.get("publisher"):
            if len(self.tool_config_names or []) != 1:
                tool_config_message = (
                    'One(1) tool config name must be supplied to publisher!'
                )
            else:
                tool_config_name = self.tool_config_names[0]
                for tool_config in self.filtered_tool_configs["publisher"]:
                    if (
                        tool_config.get('name', '').lower()
                        == tool_config_name.lower()
                    ):
                        self.logger.debug(
                            f'Using tool config {tool_config_name}'
                        )
                        if self.tool_config != tool_config:
                            self.tool_config = tool_config
                            self._progress_widget = ProgressWidget(
                                'publish', build_progress_data(tool_config)
                            )
                            self.header.set_widget(
                                self._progress_widget.status_widget
                            )
                        break
                if not self.tool_config:
                    tool_config_message = (
                        f'Could not find tool config: "{tool_config_name}"'
                    )
        else:
            tool_config_message = 'No publisher tool configs available!'

        if not self.tool_config:
            self.logger.warning(tool_config_message)
            self._scroll_area_widget.layout().addWidget(
                QtWidgets.QLabel(f'<html><i>{tool_config_message}</i></html>')
            )
            return

        # Build context widgets
        context_plugins = get_plugins(
            self.tool_config, filters={'tags': ['context']}
        )
        for context_plugin in context_plugins:
            if not context_plugin.get('ui'):
                continue
            context_widget = self.init_framework_widget(context_plugin)
            self._scroll_area_widget.layout().addWidget(context_widget)

        # Build component widgets
        component_groups = get_groups(
            self.tool_config, filters={'tags': ['component']}
        )

        for _group in component_groups:
            group_accordion_widget = AccordionBaseWidget(
                selectable=False,
                show_checkbox=True,
                checkable=_group.get('optional', False),
                title=_group.get('options').get('component'),
                selected=False,
                checked=_group.get('enabled', True),
                collapsable=True,
                collapsed=True,
            )
            collectors = get_plugins(_group, filters={'tags': ['collector']})
            self.add_collector_widgets(
                collectors, group_accordion_widget, _group
            )
            validators = get_plugins(_group, filters={'tags': ['validator']})
            self.add_validator_widgets(
                validators, group_accordion_widget, _group
            )
            exporters = get_plugins(_group, filters={'tags': ['exporter']})
            self.add_exporter_widgets(
                exporters, group_accordion_widget, _group
            )

            self._scroll_area_widget.layout().addWidget(group_accordion_widget)

        spacer = QtWidgets.QSpacerItem(
            1,
            1,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self._scroll_area_widget.layout().addItem(spacer)

    def add_collector_widgets(
        self, collectors, accordion_widget, group_config=None
    ):
        for plugin_config in collectors:
            if not plugin_config.get('ui'):
                continue
            widget = self.init_framework_widget(plugin_config, group_config)
            accordion_widget.add_widget(widget)

    def add_validator_widgets(
        self, validators, accordion_widget, group_config=None
    ):
        for plugin_config in validators:
            if not plugin_config.get('ui'):
                continue
            widget = self.init_framework_widget(plugin_config, group_config)
            accordion_widget.add_option_widget(
                widget, section_name='Validators'
            )

    def add_exporter_widgets(
        self, exporters, accordion_widget, group_config=None
    ):
        for plugin_config in exporters:
            if not plugin_config.get('ui'):
                continue
            widget = self.init_framework_widget(plugin_config, group_config)
            accordion_widget.add_option_widget(
                widget, section_name='Exporters'
            )

    def post_build_ui(self):
        pass

    def _on_run_button_clicked(self):
        '''(Override) Refresh context widget(s) upon publish'''
        self._progress_widget.run(self)
        super(StandardPublisherDialog, self)._on_run_button_clicked()
        # TODO: This will not work in remote mode (async mode) as plugin events
        #  will arrive after this point of execution.
        if self._progress_widget.status == constants.status.SUCCESS_STATUS:
            self.clean_ui()
            self.pre_build_ui()
            self.build_ui()
            self.post_build_ui()

    @invoke_in_qt_main_thread
    def plugin_run_callback(self, log_item):
        '''(Override) Pass framework log item to the progress widget'''
        if self._progress_widget:
            self._progress_widget.update_phase_status(
                log_item.plugin_reference,
                log_item.plugin_status,
                log_message=log_item.plugin_message,
                time=log_item.plugin_execution_time,
            )
