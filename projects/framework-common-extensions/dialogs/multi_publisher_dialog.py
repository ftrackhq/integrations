# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import copy
import os
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


class MultiPublisherDialog(BaseContextDialog):
    '''Default Framework Publisher dialog'''

    name = 'framework_multi_publisher_dialog'
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

        super(MultiPublisherDialog, self).__init__(
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

        multi_groups = get_groups(
            self.tool_config, filters={'tags': ['multi']}
        )
        self._accordion_widgets_registry = []
        for _group in component_groups:
            group_accordion_widget = self.add_accordion_group(_group)
            self.tool_widget.layout().addWidget(group_accordion_widget)

        for _multi_group in multi_groups:
            add_button = QtWidgets.QPushButton(
                _multi_group.get('options').get(
                    'button_label', 'Add Component'
                )
            )
            self.tool_widget.layout().addWidget(add_button)
            add_button.clicked.connect(
                partial(
                    self._on_add_component_callback, _multi_group, add_button
                )
            )

        spacer = QtWidgets.QSpacerItem(
            1,
            1,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.tool_widget.layout().addItem(spacer)
        # Create a new tool_config
        self._modified_tool_config = copy.deepcopy(self.tool_config)
        # Make sure we generate new references
        self.registry.create_unic_references(self._modified_tool_config)
        print("ya")

    def _on_add_component_callback(self, _multi_group, add_button):
        # Create a new unic group
        new_group = copy.deepcopy(_multi_group)
        # Make sure that we don't duplicate component names
        available_name = self.get_available_component_name(
            new_group.get('options').get('component')
        )
        new_group['options']['component'] = available_name
        group_accordion_widget = self.add_accordion_group(new_group)
        # Insert the new group before the add button
        add_button_idx = self.tool_widget.layout().indexOf(add_button)
        self.tool_widget.layout().insertWidget(
            add_button_idx, group_accordion_widget
        )
        # generate references for the new group
        self.registry.create_unic_references(new_group, skip_root=True)

        # Insert the new group into the correct position in the tool_config
        self.insert_group_in_tool_config(new_group, group_accordion_widget)

        # Sync the tool_config with the host
        args = {
            'tool_config': self._modified_tool_config,
        }
        self.client_method_connection('sync_tool_config', arguments=args)

        # # Add the new item into the tool config
        # args = {
        #     'tool_config_reference': self.tool_config['reference'],
        #     'section': 'engine',
        #     'new_item': _multi_group,
        # }
        # self.client_method_connection('augment_tool_config', arguments=args)

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
                self._modified_tool_config,
                filters={
                    'tags': ['component'],
                    'options': {'component': previous_widget.title},
                },
            )
            if previous_group:
                previous_group = previous_group[0]
                previous_group_idx = self._modified_tool_config[
                    'engine'
                ].index(previous_group)
                self._modified_tool_config['engine'].insert(
                    previous_group_idx + 1, new_group
                )
            else:
                self._modified_tool_config['engine'].append(new_group)
        else:
            self._modified_tool_config['engine'].insert(0, new_group)

    def get_available_component_name(self, name):
        def increment_name(name):
            if '_' in name and name.rsplit('_', 1)[-1].isdigit():
                base, num = name.rsplit('_', 1)
                return f'{base}_{int(num) + 1}'
            else:
                return f'{name}_1'

        matching_components = get_groups(
            self._modified_tool_config,
            filters={'tags': ['component'], 'options': {'component': name}},
        )
        if matching_components:
            for widget in self._accordion_widgets_registry:
                if widget.title == name:
                    return self.get_available_component_name(
                        increment_name(name)
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
        group_accordion_widget.title_changed.connect(
            self._on_component_name_changed_callback
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
        self._progress_widget.hide_overlay_signal.connect(
            self.show_main_widget
        )
        self._progress_widget.show_overlay_signal.connect(
            self.show_overlay_widget
        )

    def _on_path_changed_callback(self, accordion_widget, new_name):
        '''
        Callback to update the component name when the path is changed.
        '''
        extension = new_name.split('.')[-1] or os.path.basename(new_name)
        extension = self.get_available_component_name(extension)
        accordion_widget.set_title(extension)

    def _on_component_name_changed_callback(self, new_name):
        self.set_tool_config_option('component', new_name)

    def show_options_widget(self, widget):
        '''Sets the given *widget* as the index 2 of the stacked widget and
        remove the previous one if it exists'''
        if self._stacked_widget.widget(2):
            self._stacked_widget.removeWidget(self._stacked_widget.widget(2))
        self._stacked_widget.addWidget(widget)
        self._stacked_widget.setCurrentIndex(2)

    def _on_run_button_clicked(self):
        '''(Override) Drive the progress widget'''
        self.show_overlay_widget()
        self._progress_widget.run()
        super(MultiPublisherDialog, self)._on_run_button_clicked()
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
        super(MultiPublisherDialog, self).closeEvent(event)
