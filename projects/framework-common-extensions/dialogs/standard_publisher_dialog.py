# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_qt.widgets.accordion import AccordionBaseWidget


class StandardPublisherDialog(BaseContextDialog):
    '''Default Framework Publisher dialog'''

    name = 'framework_standard_publisher_dialog'
    tool_config_type_filter = ['publisher']
    ui_type = 'qt'
    run_button_title = 'publish'
    docked = True

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
        *dialog_options*: Dictionary of arguments passed to configure the
        current dialog.
        '''
        self._scroll_area = None
        self._scroll_area_widget = None

        super(StandardPublisherDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent,
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
        self._scroll_area_widget.setLayout(scroll_area_widget_layout)

        self.tool_widget.layout().addWidget(self._scroll_area, 100)
        self._scroll_area.setWidget(self._scroll_area_widget)

    def build_ui(self):
        # Select the desired tool_config
        if not self.filtered_tool_configs.get("publisher"):
            self.logger.warning("No Publisher tool configs available")
        else:
            self.tool_config = self.filtered_tool_configs.get("publisher")[0]

        # Build context widgets
        context_plugins = self.tool_config.get_all(
            category='plugin', plugin_type='context'
        )
        for context_plugin in context_plugins:
            if not context_plugin.widget_name:
                continue
            context_widget = self.init_framework_widget(context_plugin)
            self._scroll_area_widget.layout().addWidget(context_widget)
        # Build component widgets
        component_steps = self.tool_config.get_all(
            category='step', step_type='component'
        )
        for step in component_steps:
            # TODO: add a key visible in the tool config to hide the step if wanted.
            step_accordion_widget = AccordionBaseWidget(
                selectable=False,
                show_checkbox=True,
                checkable=not step.optional,
                title=step.step_name,
                selected=False,
                checked=step.enabled,
                collapsable=True,
                collapsed=True,
            )
            step_plugins = step.get_all(category='plugin')
            for step_plugin in step_plugins:
                if not step_plugin.widget_name:
                    continue
                widget = self.init_framework_widget(step_plugin)
                if step_plugin.plugin_type == 'collector':
                    step_accordion_widget.add_widget(widget)
                if step_plugin.plugin_type == 'validator':
                    step_accordion_widget.add_option_widget(
                        widget, section_name='Validators'
                    )
                if step_plugin.plugin_type == 'exporter':
                    step_accordion_widget.add_option_widget(
                        widget, section_name='Exporters'
                    )
            self._scroll_area_widget.layout().addWidget(step_accordion_widget)
        spacer = QtWidgets.QSpacerItem(
            1,
            1,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self._scroll_area_widget.layout().addItem(spacer)

    def post_build_ui(self):
        pass

    def run_collectors(self, plugin_widget_id=None):
        '''
        Run all the collector plugins of the current tool_config.
        If *plugin_widget_id* is given, a signal with the result of the plugins
        will be emitted to be picked by that widget id.
        '''
        collector_plugins = self.tool_config.get_all(
            category='plugin', plugin_type='collector'
        )
        for collector_plugin in collector_plugins:
            arguments = {
                "plugin_config": collector_plugin,
                "plugin_method_name": 'run',
                "engine_type": self.tool_config.engine_type,
                "engine_name": self.tool_config.engine_name,
                'plugin_widget_id': plugin_widget_id,
            }
            self.client_method_connection('run_plugin', arguments=arguments)
