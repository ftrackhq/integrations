# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_qt.widgets.accordion import AccordionBaseWidget
from ftrack_utils.framework.tool_config.read import get_plugins, get_groups


class OpenerPublisherTabDialog(BaseContextDialog):
    '''Framework Opener and Publisher in a dialog with tabs'''

    name = 'framework_standard_publisher_dialog'
    tool_config_type_filter = ['publisher', 'opener']
    ui_type = 'qt'
    run_button_title = 'publish'

    @property
    def tab_mapping(self):
        return self._tab_mapping

    @property
    def tab_widget(self):
        '''
        Return the tab widget
        '''
        return self._tab_widget

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

        super(OpenerPublisherTabDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent,
        )

        self._tab_mapping = {}
        self._tab_widget = None

        self._pre_select_tool_configs()

    def _pre_select_tool_configs(self):
        '''Pre-select the desired tool configs'''
        # Pre-select desired tool-configs
        opener_tool_configs = self.filtered_tool_configs['opener']
        if opener_tool_configs:
            # Pick the first tool config available
            self._tab_mapping['open'] = opener_tool_configs.get_first(
                tool_title="Document Opener"
            )
            if not self.tool_config:
                self.tool_config = self._tab_mapping['open']

        publisher_tool_configs = self.filtered_tool_configs['publisher']
        if publisher_tool_configs:
            # Pick the first tool config available
            self._tab_mapping['save'] = publisher_tool_configs.get_first(
                tool_title="Document Publisher"
            )
            if not self.tool_config:
                self.tool_config = self._tab_mapping['save']

    def _build_tabs(self):
        '''Build Open and save tabs'''
        if self._tab_mapping['open']:
            self._open_widget = self._build_open_widget()
            self.add_tab("Open", self._open_widget)

        if self._tab_mapping['save']:
            self._publish_widget = self._build_publish_widget()
            self.add_tab("Save", self._publish_widget)

    def _build_open_widget(self):
        '''Open tab widget creation'''
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Build Collector widget
        collector_plugins = self.tab_mapping['open'].get_all(
            category='plugin', plugin_type='collector'
        )
        for collector_plugin_config in collector_plugins:
            if not collector_plugin_config.widget_name:
                continue
            collector_widget = self.init_framework_widget(
                collector_plugin_config
            )
            collector_widget.fetch()
            main_widget.layout().addWidget(collector_widget)

        open_button = QtWidgets.QPushButton('OPEN')

        open_button.clicked.connect(self._on_ui_open_button_clicked_callback)

        main_widget.layout().addWidget(open_button)

        return main_widget

    def _build_publish_widget(self):
        '''Open tab widget creation'''
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Build Collector widget
        context_plugins = self.tab_mapping['save'].get_all(
            category='plugin', plugin_type='context'
        )
        for context_plugin_config in context_plugins:
            if not context_plugin_config.widget_name:
                continue
            context_widget = self.init_framework_widget(context_plugin_config)
            main_widget.layout().addWidget(context_widget)

        buttons_layout = QtWidgets.QHBoxLayout()

        # We create the version Up Button that will execute the
        # version up plugin
        version_up_button = QtWidgets.QPushButton('VERSION UP')
        version_up_button.clicked.connect(
            self._on_ui_version_up_button_clicked_callback
        )
        buttons_layout.addWidget(version_up_button)

        # send to review executes the entire tool-config steps/stages
        review_button = QtWidgets.QPushButton('SEND TO REVIEW')
        review_button.clicked.connect(
            self._on_ui_review_button_clicked_callback
        )
        buttons_layout.addWidget(review_button)

        main_widget.layout().addLayout(buttons_layout)

        return main_widget

    def pre_build_ui(self):
        pass

    def build_ui(self):
        # Select the desired tool_config

        self._tab_widget = QtWidgets.QTabWidget()
        self._build_tabs()
        self.layout().addWidget(self._tab_widget)

        self.run_button.setVisible(False)

    def add_collector_widgets(self, collectors, accordion_widget):
        for plugin in collectors:
            if not plugin.get('ui'):
                continue
            widget = self.init_framework_widget(plugin)
            accordion_widget.add_widget(widget)

    def add_validator_widgets(self, validators, accordion_widget):
        for plugin in validators:
            if not plugin.get('ui'):
                continue
            widget = self.init_framework_widget(plugin)
            accordion_widget.add_option_widget(
                widget, section_name='Validators'
            )

    def add_exporter_widgets(self, exporters, accordion_widget):
        for plugin in exporters:
            if not plugin.get('ui'):
                continue
            widget = self.init_framework_widget(plugin)
            accordion_widget.add_option_widget(
                widget, section_name='Exporters'
            )

    def post_build_ui(self):
        self._tab_widget.currentChanged.connect(
            self._on_selected_tab_changed_callback
        )

    def _on_selected_tab_changed_callback(self, tab_name):
        if not tab_name:
            self.tool_config = None
            return
        self.tool_config = self.tab_mapping.get(tab_name.lower())

    def run_collectors(self, plugin_widget_id=None):
        '''
        Run all the collector plugins of the current tool_config.
        If *plugin_widget_id* is given, a signal with the result of the plugins
        will be emitted to be picked by that widget id.
        '''
        collector_plugins = get_plugins(
            self.tool_config, filters={'tags': ['collector']}
        )
        for collector_plugin in collector_plugins:
            arguments = {
                "plugin_config": collector_plugin,
                "plugin_method_name": 'run',
                "engine_type": self.tool_config['engine_type'],
                "engine_name": self.tool_config['engine_name'],
                'plugin_widget_id': plugin_widget_id,
            }
            self.client_method_connection('run_plugin', arguments=arguments)
