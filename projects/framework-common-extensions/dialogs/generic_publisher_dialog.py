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
from ftrack_qt.widgets.accordion import AccordionBaseWidget
from ftrack_qt.widgets.progress import ProgressWidget
from ftrack_qt.utils.widget import build_progress_data
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread
from ftrack_qt.widgets.buttons import CircularButton
from ftrack_qt.widgets.buttons import MenuButton


class GenericPublisherDialog(BaseContextDialog):
    '''Default Framework Publisher dialog'''

    name = 'framework_generic_publisher_dialog'
    tool_config_type_filter = ['publisher']
    ui_type = 'qt'
    run_button_title = 'PUBLISH'

    @property
    def modified_tool_config(self):
        '''Return the modified tool config'''
        return self._modified_tool_config

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

        super(GenericPublisherDialog, self).__init__(
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

        # Create a new tool_config
        self._original_tool_config = self.tool_config
        self._modified_tool_config = copy.deepcopy(self._original_tool_config)
        # Make sure we generate new references
        self.registry.create_unic_references(self._modified_tool_config)
        self.tool_config = self._modified_tool_config

        # Sync the tool_config with the host
        self.sync_tool_config(self.tool_config)

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

        component_groups = get_groups(
            self.tool_config, filters={'tags': ['component']}
        )

        generic_groups = get_groups(
            self._original_tool_config, filters={'tags': ['generic']}
        )
        self._accordion_widgets_registry = []
        for _group in component_groups:
            group_accordion_widget = self.add_accordion_group(_group)
            self.tool_widget.layout().addWidget(group_accordion_widget)

        circular_add_button = CircularButton('add', variant='outlined')
        self.menu_button = MenuButton(circular_add_button)
        self.tool_widget.layout().addWidget(self.menu_button)
        for _generic_group in generic_groups:
            self.menu_button.add_item(
                item_data=_generic_group,
                label=_generic_group.get('options').get(
                    'button_label', 'Add Component'
                ),
            )
        self.menu_button.item_clicked.connect(self._on_add_component_callback)

        spacer = QtWidgets.QSpacerItem(
            1,
            1,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.tool_widget.layout().addItem(spacer)

    def _get_latest_component_index(self, idx=1):
        # Get the number of items in the layout
        count = self.tool_widget.layout().count()
        if count > 0:
            # Get the last item
            item = self.tool_widget.layout().itemAt(count - idx)
            if item:
                if item.widget() in self._accordion_widgets_registry:
                    # Return the widget associated with the item
                    return self.tool_widget.layout().indexOf(item.widget())
                else:
                    return self._get_latest_component_index(idx + 1)
        return 0

    def _on_add_component_callback(self, _generic_group):
        # Create a new unic group
        new_group = copy.deepcopy(_generic_group)
        # Make sure that we don't duplicate component names
        available_name = self.get_available_component_name(
            new_group.get('options').get('component')
        )
        new_group['options']['component'] = available_name

        # generate references for the new group
        self.registry.create_unic_references(new_group, skip_root=True)

        group_accordion_widget = self.add_accordion_group(new_group)

        # Insert the new group before the add button
        latest_idx = self._get_latest_component_index()
        self.tool_widget.layout().insertWidget(
            latest_idx + 1, group_accordion_widget
        )

        # Insert the new group into the correct position in the tool_config
        self.insert_group_in_tool_config(new_group, group_accordion_widget)

        # Sync the tool_config with the host
        self.sync_tool_config(self.tool_config)

        self._progress_widget.set_data(build_progress_data(self.tool_config))

    def insert_group_in_tool_config(self, new_group, group_accordion_widget):
        '''
        Insert the new group in the tool config in the right position.
        '''
        current_idx = self._accordion_widgets_registry.index(
            group_accordion_widget
        )
        if current_idx > 0:
            previous_widget = self._accordion_widgets_registry[current_idx - 1]
            previous_group = get_groups(
                self.tool_config,
                filters={
                    'tags': ['component'],
                    'options': {'component': previous_widget.title},
                },
            )
            if previous_group:
                previous_group = previous_group[0]
                previous_group_idx = self.tool_config['engine'].index(
                    previous_group
                )
                self.tool_config['engine'].insert(
                    previous_group_idx + 1, new_group
                )
            else:
                self.tool_config['engine'].append(new_group)
        else:
            self.tool_config['engine'].insert(0, new_group)

    def get_available_component_name(self, name, skip_widget=None):
        def increment_name(name):
            if '_' in name and name.rsplit('_', 1)[-1].isdigit():
                base, num = name.rsplit('_', 1)
                return f'{base}_{int(num) + 1}'
            else:
                return f'{name}_1'

        for widget in self._accordion_widgets_registry:
            if widget != skip_widget:
                if widget.title == name:
                    return self.get_available_component_name(
                        increment_name(name), skip_widget
                    )
        return name

    def add_accordion_group(self, group):
        group_accordion_widget = AccordionBaseWidget(
            selectable=False,
            show_checkbox=True,
            checkable=group.get('optional', False),
            title=group.get('options').get('component'),
            editable_title=group.get('options', {}).get(
                'editable_component_name', False
            ),
            selected=False,
            checked=group.get('enabled', True),
            collapsable=True,
            collapsed=True,
            removable=group.get('options', {}).get('removable', False),
        )
        collectors = get_plugins(group, filters={'tags': ['collector']})
        self.add_collector_widgets(collectors, group_accordion_widget, group)
        validators = get_plugins(group, filters={'tags': ['validator']})
        self.add_validator_widgets(validators, group_accordion_widget, group)
        exporters = get_plugins(group, filters={'tags': ['exporter']})
        self.add_exporter_widgets(exporters, group_accordion_widget, group)
        group_accordion_widget.hide_options_overlay.connect(
            self.show_main_widget
        )
        group_accordion_widget.show_options_overlay.connect(
            self.show_options_widget
        )
        group_accordion_widget.title_edited.connect(
            self._on_component_name_edited_callback
        )
        group_accordion_widget.bin_clicked.connect(
            self._on_component_removed_callback
        )
        group_accordion_widget.enabled_changed.connect(
            partial(self._on_enable_component_changed_callback, group)
        )

        self._accordion_widgets_registry.append(group_accordion_widget)
        return group_accordion_widget

    def add_collector_widgets(
        self, collectors, accordion_widget, group_config=None
    ):
        for plugin_config in collectors:
            if not plugin_config.get('ui'):
                continue
            widget = self.init_framework_widget(plugin_config, group_config)
            accordion_widget.add_widget(widget)
            if hasattr(widget, 'path_changed'):
                if group_config.get('options', {}).get(
                    'editable_component_name', False
                ):
                    widget.path_changed.connect(
                        partial(
                            self._on_path_changed_callback, accordion_widget
                        )
                    )

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
        self._save_preset_button.clicked.connect(
            self._on_save_preset_button_clicked
        )

    def _on_path_changed_callback(self, accordion_widget, new_name):
        '''
        Callback to update the component name when the path is changed.
        '''
        file_extension = None
        try:
            collection = clique.parse(new_name)
            if collection:
                file_extension = collection.tail
        except Exception as error:
            self.logger.debug(
                f"{new_name} is not a clique collection. Error {error}"
            )

        if not file_extension:
            file_extension = os.path.splitext(new_name)[1] or os.path.basename(
                new_name
            )

        file_extension = file_extension.lstrip('.')

        extension = self.get_available_component_name(file_extension)

        group = get_groups(
            self.tool_config,
            filters={
                'tags': ['component'],
                'options': {'component': accordion_widget.title},
            },
        )[0]
        group['options']['component'] = extension

        accordion_widget.set_title(extension)

        # Sync the tool_config with the host
        self.sync_tool_config(self.tool_config)

    def _on_component_name_edited_callback(self, new_name):
        new_name = self.get_available_component_name(
            new_name, skip_widget=self.sender()
        )
        if self.sender().previous_title:
            group = get_groups(
                self.tool_config,
                filters={
                    'tags': ['component'],
                    'options': {'component': self.sender().previous_title},
                },
            )[0]
            group['options']['component'] = new_name

        self.sender().set_title(new_name)

        # Sync the tool_config with the host
        self.sync_tool_config(self.tool_config)

    def _on_component_removed_callback(self, event):
        # Remove the group from the tool_config
        group = get_groups(
            self.tool_config,
            filters={
                'tags': ['component'],
                'options': {'component': self.sender().title},
            },
        )
        if group:
            group = group[0]
            self.tool_config['engine'].remove(group)
        # Remove the widget from the registry
        self._accordion_widgets_registry.remove(self.sender())
        # Remove the widget from the layout
        self.sender().teardown()
        self.sender().deleteLater()

        # Sync the tool_config with the host
        self.sync_tool_config(self.tool_config)

        self._progress_widget.set_data(build_progress_data(self.tool_config))

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
        # Sync the tool_config with the host
        self.sync_tool_config(self.tool_config)

        self._progress_widget.set_data(build_progress_data(self.tool_config))

    def _on_run_button_clicked(self):
        '''(Override) Drive the progress widget'''
        self.show_overlay_widget()
        self._progress_widget.run()
        super(GenericPublisherDialog, self)._on_run_button_clicked()
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
        if self._accordion_widgets_registry:
            for accordion in self._accordion_widgets_registry:
                accordion.teardown()
        super(GenericPublisherDialog, self).closeEvent(event)
