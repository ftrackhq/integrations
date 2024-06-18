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
        for entry in self.dialog_options.get('event_data', {}).get(
            'selection', []
        ):
            result.append(
                {
                    'entity_id': entry['entityId'],
                    'entity_type': entry['entityType'],
                }
            )
        return result

    def is_compatible(self, tool_config, component):
        '''Check if the *tool_config* is compatible with provided *component* entity,
        returns True if compatible, False or error message as string otherwise
        '''
        compatible = tool_config.get('compatible')
        if not compatible:
            return f'Tool config {tool_config} is missing required loader "compatible" entry!'
        # Filter on combination of component name, asset_type and file extension
        result = False
        if compatible.get('component'):
            # Component name match?
            if compatible['component'].lower() == component['name'].lower():
                result = True
            else:
                self.logger.debug(
                    f"Component {compatible['component']} doesn't match {component['name']}"
                )
                return False
        if compatible.get('asset_type'):
            # Asset type match?
            asset = component['version']['asset']
            asset_type = asset['type']['name']
            if compatible['asset_type'].lower() == asset_type.lower():
                result = True
            else:
                self.logger.debug(
                    f"Asset type {compatible['asset_type']} doesn't match {asset_type}"
                )
                return False
        if compatible.get('supported_file_extensions'):
            # Any file extension match?
            result = False
            file_extension = component['file_type']
            for file_type in compatible.get('supported_file_extensions'):
                if file_type.lower() == file_extension.lower():
                    result = True
                    break
            if not result:
                self.logger.debug(
                    f"File extensions {compatible['supported_file_extensions']} doesn't match component: {file_extension}"
                )
                return False
        if compatible.get('entity_types'):
            result = False
            for entity_type in compatible['entity_types']:
                if component.entity_type == entity_type:
                    result = True
                    break
            if not result:
                self.logger.debug(
                    f"Component {component['name']} entity type {component.entity_type} doesn't match {compatible['entity_types']}"
                )
                return False
        if not result:
            self.logger.debug(
                f'Tool config {tool_config} is not compatible with component'
            )
        return result

    def pre_build_ui(self):
        pass

    def build_ui(self):
        # Check entities
        # Select the desired tool_config
        tool_config_message = None
        if 'event_data' not in self.dialog_options:
            tool_config_message = 'No event data provided!'
        elif not self.get_entities():
            tool_config_message = 'No entity provided to load!'
        elif len(self.get_entities()) != 1:
            tool_config_message = 'Only one entity supported!'
        elif self.get_entities()[0]['entity_type'].lower() != 'component':
            tool_config_message = 'Only components can be loaded'
        elif self.filtered_tool_configs.get("loader"):
            component_id = self.get_entities()[0]['entity_id']
            component = self.session.query(
                f'Component where id={component_id}'
            ).first()

            if not component:
                tool_config_message = f'Component not found: {component_id}'
            else:
                # Loop through tool configs, find a one that can load the component in question
                for tool_config in self.filtered_tool_configs["loader"]:
                    result = self.is_compatible(tool_config, component)
                    if result is not True:
                        if isinstance(result, str):
                            # Unrecoverable error
                            tool_config_message = result
                            break
                    else:
                        tool_config_name = tool_config['name']
                        self.logger.debug(
                            f'Using tool config {tool_config_name}'
                        )
                        if self.tool_config != tool_config:
                            try:
                                self.tool_config = tool_config
                            except Exception as error:
                                tool_config_message = error
                                break
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
                    tool_config_message = f'Could not find a tool config compatible with the component {component_id}!'
        else:
            tool_config_message = 'No loader tool configs available!'

        if not self.tool_config:
            self.logger.warning(tool_config_message)
            label_widget = QtWidgets.QLabel(f'{tool_config_message}')
            label_widget.setStyleSheet(
                "font-style: italic; font-weight: bold; color: red;"
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
            # Inject the entity data into the context plugin
            if 'options' not in context_plugin:
                context_plugin['options'] = {}
            context_plugin['options'].update(self.dialog_options)
            context_widget = self.init_framework_widget(context_plugin)
            self.tool_widget.layout().addWidget(context_widget)

        # Build human readable loader name from tool config name
        loader_name_widget = QtWidgets.QWidget()
        loader_name_widget.setLayout(QtWidgets.QHBoxLayout())

        label = QtWidgets.QLabel('Loader:')
        label.setProperty('secondary', True)
        loader_name_widget.layout().addWidget(label)

        label = QtWidgets.QLabel(
            self.tool_config['name'].replace('-', ' ').title()
        )
        label.setProperty('h2', True)
        loader_name_widget.layout().addWidget(label, 100)

        self.tool_widget.layout().addWidget(loader_name_widget)

        # Add loader plugin(s)
        loader_plugins = get_plugins(
            self.tool_config, filters={'tags': ['loader']}
        )
        # Expect only one for now
        if len(loader_plugins) != 1:
            raise Exception('Only one(1) loader plugin is supported!')

        for loader_plugin in loader_plugins:
            options = loader_plugin.get('options', {})
            if not loader_plugin.get('ui'):
                continue
            loader_widget = self.init_framework_widget(loader_plugin)
            self.tool_widget.layout().addWidget(loader_widget)

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
        self._progress_widget.run()
        super(StandardLoaderDialog, self)._on_run_button_clicked()

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
        if self._progress_widget:
            self._progress_widget.teardown()
            self._progress_widget.deleteLater()
        super(StandardLoaderDialog, self).closeEvent(event)
