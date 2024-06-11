# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os.path

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_utils.framework.config.tool import get_plugins, get_groups
from ftrack_utils.string import str_version
from ftrack_framework_qt.dialogs import BaseDialog
from ftrack_qt.widgets.progress import ProgressWidget
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread
from ftrack_qt.utils.widget import build_progress_data


class StandardLoaderDialog(BaseDialog):
    '''Default Framework Loader dialog'''

    name = 'framework_standard_loader_dialog'
    tool_config_type_filter = ['loader']
    ui_type = 'qt'
    run_button_title = 'LOAD'

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
        Initialize Mixin class loader dialog. It will load the qt dialog and
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

        super(StandardLoaderDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=parent,
        )
        self.resize(400, 450)
        self.setWindowTitle('ftrack Loader')

    def get_entities(self):
        '''Get the entities to load from dialog options'''
        result = []
        for entry in self.dialog_options['event_data'].get('selection'):
            result.append(
                {
                    'entity_id': entry['entity_id'],
                    'entity_type': entry['entity_type'],
                }
            )
        return result

    def pre_build_ui(self):
        pass

    def _show_error(self, error_message):
        self.logger.warning(error_message)
        label_widget = QtWidgets.QLabel(f'{error_message}')
        label_widget.setStyleSheet(
            "font-style: italic; font-weight: bold; color: red;"
        )
        self.tool_widget.layout().addWidget(label_widget)

    def build_ui(self):
        # Check entities
        if not self.get_entities():
            self._show_error('No entities provided!')
            return
        # Select the desired tool_config
        tool_config_message = None
        if self.filtered_tool_configs.get("loader"):
            if len(self.tool_config_names or []) != 1:
                tool_config_message = (
                    'One(1) tool config name must be supplied to loader!'
                )
            else:
                tool_config_name = self.tool_config_names[0]
                for tool_config in self.filtered_tool_configs["loader"]:
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
                            if False:
                                self._progress_widget = ProgressWidget(
                                    'load', build_progress_data(tool_config)
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
            tool_config_message = 'No loader tool configs available!'

        if not self.tool_config:
            self._show_error(tool_config_message)
            return

        # Currently we support only one entity
        record = self.get_entities()[0]
        entity_id = record.get('entity_id')
        entity_type = record.get('entity_type')

        if entity_type != 'component':
            self._show_error('Only components are supported!')
            return

        ft_component = self.session.query(
            f'Component where id={entity_id}'
        ).first()
        if not ft_component:
            self._show_error(f'Component not found: {entity_id}!')
            return

        label = QtWidgets.QLabel('Asset to load:')
        label.setProperty('highlighted', True)
        self.tool_widget.layout().addWidget(label)

        asset_path_label = QtWidgets.QLabel(
            f'{str_version(ft_component["version"])} / {ft_component["name"]}'
        )
        asset_path_label.setProperty('h3', True)
        self.tool_widget.layout().addWidget(asset_path_label)

        ft_location = self.session.pick_location()

        # Build component widgets with loader options, based on what we can support
        # and the entities provided
        component_groups = get_groups(
            self.tool_config, filters={'tags': ['component']}
        )

        # Find a loader that matches
        for group_config in component_groups:
            options = group_config.get('options')
            if not options:
                self.logger.warning(
                    f'Component {group_config} are missing required loader options!'
                )
                return
            compatible = False
            if 'component' in options:
                # Component name match?
                if (
                    options['component'].lower()
                    == ft_component['name'].lower()
                ):
                    compatible = True
                else:
                    self.logger.debug(
                        f"Component {options['component']} doesn't match {ft_component['name']}"
                    )
                    continue
            if 'asset_type' in options:
                # Asset type match?
                asset = ft_component['version']['asset']
                asset_type = asset['type']['name']
                if options['asset_type'].lower() == asset_type.lower():
                    compatible = True
                else:
                    self.logger.debug(
                        f"Asset type {options['asset_type']} doesn't match {asset_type}"
                    )
                    continue
            if 'file_types' in options:
                # Any file extension match?
                file_extension = ft_component['file_type']
                for file_type in options['file_types']:
                    if file_type.lower() == file_extension.lower():
                        compatible = True
                        break
                if not compatible:
                    self.logger.debug(
                        f"File extensions {options['file_types']} doesn't match component: {file_extension}"
                    )
                    continue
            if compatible:
                # Get component path
                component_path = ft_location.get_filesystem_path(ft_component)

                component_name = ft_component['name']
                loader_name = options.get('name')

                label = QtWidgets.QLabel('Loader:')
                label.setProperty('highlighted', True)
                self.tool_widget.layout().addWidget(label)

                loader_label = QtWidgets.QLabel(f'{loader_name}')
                loader_label.setProperty('h3', True)
                loader_label.setToolTip(
                    f"The component to be loaded is {component_name}({ft_component['id']}) using loader {loader_name}: {component_path}"
                )
                self.tool_widget.layout().addWidget(loader_label)

                # Path exists?
                if not os.path.exists(component_path):
                    self._show_error(f'Path not found: {component_path}')
                    return

                label = QtWidgets.QLabel('Path:')
                label.setProperty('highlighted', True)
                self.tool_widget.layout().addWidget(label)

                path_label = QtWidgets.QLabel(f'{component_path}')
                path_label.setProperty('h3', True)
                path_label.setToolTip(
                    f'Location: {ft_location["name"]} ({ft_location["id"]})'
                )
                self.tool_widget.layout().addWidget(path_label)

                # Any UI:s?
                plugins = get_plugins(group_config)
                for plugin_config in plugins:
                    if not plugin_config.get('ui'):
                        continue
                    widget = self.init_framework_widget(
                        plugin_config, group_config
                    )
                    self.tool_widget.layout().addWidget(widget)
            else:
                self.logger.debug(
                    f'Loader {group_config} is not compatible with component {ft_component["name"]}'
                )

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

    def _on_run_button_clicked(self):
        '''(Override) Drive the progress widget'''
        self.show_overlay_widget()
        if self._progress_widget:
            self._progress_widget.run()
        super(StandardLoaderDialog, self)._on_run_button_clicked()

    @invoke_in_qt_main_thread
    def plugin_run_callback(self, log_item):
        '''(Override) Pass framework log item to the progress widget'''
        if self._progress_widget:
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
        super(StandardLoaderDialog, self).closeEvent(event)
