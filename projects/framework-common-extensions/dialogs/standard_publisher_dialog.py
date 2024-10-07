# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from functools import partial

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

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

    def __init__(
        self,
        event_manager,
        client_id,
        connect_methods_callback,
        connect_setter_property_callback,
        connect_getter_property_callback,
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
        *dialog_options*: Dictionary of arguments passed on to configure the
        current dialog.
        '''
        self._scroll_area = None
        self._scroll_area_widget = None
        self._progress_widget = None
        self._accordion_widgets_registry = []

        super(StandardPublisherDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=parent,
        )
        self.setWindowTitle('ftrack Publisher')

    def pre_build_ui(self):
        # Make sure to remove self._scroll_area in case of reload
        if self._scroll_area:
            self._scroll_area.deleteLater()
        # Create scroll area to add all the widgets
        self._scroll_area = QtWidgets.QScrollArea()
        self._scroll_area.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff
        )

        index = self.main_layout.indexOf(self.tool_widget)
        run_index = self.main_layout.indexOf(self.run_button)
        if index != -1:  # Ensure the widget is found in the layout
            # Remove the old widget from layout
            self.main_layout.takeAt(index)
            # Insert the new widget at the same position
            self.main_layout.insertWidget(index, self._scroll_area)
        elif run_index != -1:
            # In case tool_widget is not already parented make sure to add scroll
            # area above the run button.
            self.main_layout.insertWidget((run_index - 1), self._scroll_area)
        else:  # otherwise set it at the end
            self.main_layout.addWidget(self._scroll_area)

        self._scroll_area.setWidget(self.tool_widget)

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
                            try:
                                self.tool_config = tool_config
                            except Exception as error:
                                tool_config_message = error
                                break
                            if not self._progress_widget:
                                self._progress_widget = ProgressWidget(
                                    'publish', build_progress_data(tool_config)
                                )
                                self.header.set_widget(
                                    self._progress_widget.status_widget
                                )
                                self.overlay_layout.addWidget(
                                    self._progress_widget.overlay_widget
                                )
                        break
                if not self.tool_config and not tool_config_message:
                    tool_config_message = (
                        f'Could not find tool config: "{tool_config_name}"'
                    )
        else:
            tool_config_message = 'No publisher tool configs available!'

        if not self.tool_config:
            self.logger.warning(tool_config_message)
            label_widget = QtWidgets.QLabel(f'{tool_config_message}')
            label_widget.setStyleSheet(
                "font-style: italic; font-weight: bold;"
            )
            self.tool_widget.layout().addWidget(label_widget)
            self.run_button.setEnabled(False)
            return

        # Build context widgets
        context_plugins = get_plugins(
            self.tool_config, filters={'tags': ['context']}
        )
        for context_plugin in context_plugins:
            if not context_plugin.get('ui'):
                continue
            context_widget = self.init_framework_widget(context_plugin)
            self.tool_widget.layout().addWidget(context_widget)

        # Build component widgets

        self.tool_widget.layout().addWidget(QtWidgets.QLabel('Components'))

        component_groups = get_groups(
            self.tool_config, filters={'tags': ['component']}
        )

        self._accordion_widgets_registry = []
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

            self.tool_widget.layout().addWidget(group_accordion_widget)
            group_accordion_widget.hide_options_overlay.connect(
                self.show_main_widget
            )
            group_accordion_widget.show_options_overlay.connect(
                self.show_options_widget
            )
            group_accordion_widget.enabled_changed.connect(
                partial(self._on_enable_component_changed_callback, _group)
            )
            self._accordion_widgets_registry.append(group_accordion_widget)

        spacer = QtWidgets.QSpacerItem(
            1,
            1,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.tool_widget.layout().addItem(spacer)

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
        if self._progress_widget:
            self._progress_widget.hide_overlay_signal.connect(
                self.show_main_widget
            )
            self._progress_widget.show_overlay_signal.connect(
                self.show_overlay_widget
            )

    def show_options_widget(self, widget):
        '''Sets the given *widget* as the index 2 of the stacked widget and
        remove the previous one if it exists'''
        if self._stacked_widget.widget(2):
            self._stacked_widget.removeWidget(self._stacked_widget.widget(2))
        self._stacked_widget.addWidget(widget)
        self._stacked_widget.setCurrentIndex(2)

    def _on_enable_component_changed_callback(self, group_config, enabled):
        '''Callback for when the component is enabled/disabled'''
        self.set_tool_config_option(
            {'enabled': enabled}, group_config['reference']
        )
        group_config['enabled'] = enabled
        self._progress_widget.set_data(build_progress_data(self.tool_config))

    def _on_run_button_clicked(self):
        '''(Override) Drive the progress widget'''
        self.show_overlay_widget()
        self._progress_widget.run()
        super(StandardPublisherDialog, self)._on_run_button_clicked()
        # TODO: This will not work in remote mode (async mode) as plugin events
        #  will arrive after this point of execution.
        if self._progress_widget.status == constants.status.SUCCESS_STATUS:
            self.clean_ui()
            self.pre_build_ui()
            self.build_ui()
            self.post_build_ui()
            # TODO: there is an error here showing the overlay widget because is not repainting all the widegts that has been parented to the self.layout() in the pre_build_ui build_ui or post_build_ui methods.

    @invoke_in_qt_main_thread
    def plugin_run_callback(self, log_item):
        '''(Override) Pass framework log item to the progress widget'''
        self._progress_widget.update_phase_status(
            log_item.reference,
            log_item.status,
            log_message=log_item.message,
            time=log_item.execution_time,
        )

    def closeEvent(self, event):
        '''(Override) Close the context and progress widgets'''
        if self._context_selector:
            self._context_selector.teardown()
        if self._progress_widget:
            self._progress_widget.teardown()
            self._progress_widget.deleteLater()
        if self._accordion_widgets_registry:
            for accordion in self._accordion_widgets_registry:
                accordion.teardown()
        super(StandardPublisherDialog, self).closeEvent(event)
