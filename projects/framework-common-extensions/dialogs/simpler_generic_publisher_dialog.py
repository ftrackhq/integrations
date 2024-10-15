# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import copy
import os
from functools import partial

import clique

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

import ftrack_constants as constants
from ftrack_utils.framework.config.tool import get_plugins, get_groups
from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_qt.widgets.progress import ProgressWidget
from ftrack_qt.utils.widget import build_progress_data
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread


class SimplerGenericPublisherDialog(BaseContextDialog):
    '''Default Framework Publisher dialog'''

    name = 'simpler_framework_generic_publisher_dialog'
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
        self._modified_tool_config = None
        self._save_preset_button = None

        super(SimplerGenericPublisherDialog, self).__init__(
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
        # Build top label layout
        components_layout = QtWidgets.QHBoxLayout()
        components_label = QtWidgets.QLabel('Components')
        self._save_preset_button = QtWidgets.QPushButton('Save Preset')
        components_layout.addWidget(components_label)
        components_layout.addStretch()
        components_layout.addWidget(self._save_preset_button)
        self.tool_widget.layout().addLayout(components_layout)

        collector_plugins = get_plugins(
            self.tool_config, filters={'tags': ['collector']}
        )
        for collector_plugin in collector_plugins:
            if not collector_plugin.get('ui'):
                continue
            collector_widget = self.init_framework_widget(collector_plugin)
            self.tool_widget.layout().addWidget(collector_widget)

        spacer = QtWidgets.QSpacerItem(
            1,
            1,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.tool_widget.layout().addItem(spacer)

    def post_build_ui(self):
        if self._progress_widget:
            self._progress_widget.hide_overlay_signal.connect(
                self.show_main_widget
            )
            self._progress_widget.show_overlay_signal.connect(
                self.show_overlay_widget
            )
        self._save_preset_button.clicked.connect(
            self._on_save_preset_button_clicked
        )

    def _on_run_button_clicked(self):
        '''(Override) Drive the progress widget'''
        self.show_overlay_widget()
        self._progress_widget.run()
        super(SimplerGenericPublisherDialog, self)._on_run_button_clicked()
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

    def _on_save_preset_button_clicked(self):
        '''Callback to save the current tool config as a preset'''
        # Open a save dialog to get the destination
        destination = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save Tool Config Preset', '', 'YAML (*.yaml)'
        )[0]
        args = {
            'tool_config': self.tool_config,
            'destination': destination,
        }
        self.client_method_connection(
            'save_tool_config_in_destination', arguments=args
        )

    def closeEvent(self, event):
        '''(Override) Close the context and progress widgets'''
        if self._context_selector:
            self._context_selector.teardown()
        if self._progress_widget:
            self._progress_widget.teardown()
            self._progress_widget.deleteLater()
        super(SimplerGenericPublisherDialog, self).closeEvent(event)
