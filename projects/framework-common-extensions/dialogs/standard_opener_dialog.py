# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_utils.framework.config.tool import get_plugins, get_groups
from ftrack_qt.widgets.progress import ProgressWidget
from ftrack_qt.utils.decorators import invoke_in_qt_main_thread
from ftrack_qt.utils.widget import build_progress_data


class StandardOpenerDialog(BaseContextDialog):
    '''Default Framework Opener dialog'''

    name = 'framework_standard_opener_dialog'
    tool_config_type_filter = ['opener']
    ui_type = 'qt'
    run_button_title = 'OPEN'

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
        Initialize Mixin class opener dialog. It will load the qt dialog and
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

        super(StandardOpenerDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=parent,
        )
        self.resize(400, 450)
        self.setWindowTitle('ftrack Opener')

    def pre_build_ui(self):
        pass

    def build_ui(self):
        # Select the desired tool_config
        tool_config_message = None
        if self.filtered_tool_configs.get("opener"):
            if len(self.tool_config_names or []) != 1:
                tool_config_message = (
                    'One(1) tool config name must be supplied to opener!'
                )
            else:
                tool_config_name = self.tool_config_names[0]
                for tool_config in self.filtered_tool_configs["opener"]:
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
                            self._progress_widget = ProgressWidget(
                                'open', build_progress_data(tool_config)
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
            tool_config_message = 'No opener tool configs available!'

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

        # Build component widgets with asset version selector
        component_groups = get_groups(
            self.tool_config, filters={'tags': ['component']}
        )

        for group_config in component_groups:
            component_name = group_config.get('options').get('component')
            component_label = QtWidgets.QLabel(f"Component: {component_name}")
            component_label.setProperty('h3', True)
            component_label.setToolTip(
                f"The component to be open is {component_name}"
            )
            self.tool_widget.layout().addWidget(component_label)

            collectors = get_plugins(
                group_config, filters={'tags': ['collector']}
            )
            for plugin_config in collectors:
                if not plugin_config.get('ui'):
                    continue
                widget = self.init_framework_widget(
                    plugin_config, group_config
                )

                self.tool_widget.layout().addWidget(widget)

        spacer = QtWidgets.QSpacerItem(
            1,
            1,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self.tool_widget.layout().addItem(spacer)

    def post_build_ui(self):
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
        super(StandardOpenerDialog, self)._on_run_button_clicked()

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
        super(StandardOpenerDialog, self).closeEvent(event)
