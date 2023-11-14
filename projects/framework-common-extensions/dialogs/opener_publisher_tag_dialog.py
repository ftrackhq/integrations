# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_qt.widgets.accordion import AccordionBaseWidget
from ftrack_utils.framework.tool_config.read import get_plugins, get_groups


class OpenerPublisherTabDialog(BaseContextDialog):
    '''Framework Opener and Publisher in a dialog with tabs'''

    name = 'framework_opener_publisher_tab_dialog'
    tool_config_type_filter = ['publisher', 'opener']
    ui_type = 'qt'
    run_button_title = None

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
        self._tab_mapping = {}
        self._tab_widget = None

        super(OpenerPublisherTabDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent,
        )

        self._pre_select_tool_configs()

    def _pre_select_tool_configs(self):
        '''Pre-select the desired tool configs'''
        # Pre-select desired tool-configs
        opener_tool_configs = self.filtered_tool_configs['opener']
        if opener_tool_configs:
            # Pick the first tool config available
            self._tab_mapping['open'] = opener_tool_configs[0]

        publisher_tool_configs = self.filtered_tool_configs['publisher']
        if publisher_tool_configs:
            # Pick the first tool config available
            self._tab_mapping['save'] = publisher_tool_configs[0]

    def add_tab(self, tab_title, widget):
        self._tab_widget.addTab(widget, tab_title)

    def _build_tabs(self):
        '''Build Open and save tabs'''
        self._open_widget = self._build_open_widget(
            self._tab_mapping.get('open')
        )
        self.add_tab("Open", self._open_widget)

        self._publish_widget = self._build_publish_widget(
            self._tab_mapping.get('save')
        )
        self.add_tab("Save", self._publish_widget)

    def _build_open_widget(self, tool_config):
        '''Open tab widget creation'''
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Build Collector widget
        open_button = QtWidgets.QPushButton('OPEN')

        if tool_config:
            collector_plugins = get_plugins(
                tool_config, filters={'tags': ['collector']}
            )
            for collector_plugin in collector_plugins:
                if not collector_plugin.get('ui'):
                    continue
                collector_widget = self.init_framework_widget(collector_plugin)
                # TODO: run ui hook
                # collector_widget.fetch()
                main_widget.layout().addWidget(collector_widget)
        else:
            main_widget.layout().addWidget(
                QtWidgets.QLabel(
                    '<html><i>No open tool config available</i></html>'
                )
            )
            open_button.setDisabled(True)

        open_button.clicked.connect(self._on_run_button_clicked)

        main_widget.layout().addWidget(open_button)

        return main_widget

    def _on_selected_tab_changed_callback(self, tab_index):
        self.tool_config = self.tab_mapping.get(
            'open' if tab_index == 0 else 'save'
        )

    def _build_publish_widget(self, tool_config):
        '''Open tab widget creation'''
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        main_widget.setLayout(main_layout)

        publish_button = QtWidgets.QPushButton('PUBLISH')

        if tool_config:
            # Build Collector widget
            context_plugins = get_plugins(
                tool_config or {}, filters={'tags': ['context']}
            )
            for context_plugin in context_plugins:
                if not context_plugin.get('ui'):
                    continue
                context_widget = self.init_framework_widget(context_plugin)
                main_widget.layout().addWidget(context_widget)
        else:
            main_widget.layout().addWidget(
                QtWidgets.QLabel(
                    '<html><i>No publish tool config available</i></html>'
                )
            )
            publish_button.setDisabled(True)

        buttons_layout = QtWidgets.QHBoxLayout()

        # send to review executes the entire tool-config steps/stages
        publish_button.clicked.connect(self._on_run_button_clicked)
        buttons_layout.addWidget(publish_button)

        main_widget.layout().addLayout(buttons_layout)

        return main_widget

    def pre_build_ui(self):
        pass

    def build_ui(self):
        # Select the desired tool_config

        self._tab_widget = QtWidgets.QTabWidget()
        self._build_tabs()
        self.tool_widget.layout().addWidget(self._tab_widget)

        self.run_button.setVisible(False)

    def post_build_ui(self):
        self._tab_widget.currentChanged.connect(
            self._on_selected_tab_changed_callback
        )

    def _on_ui_run_button_clicked_callback(self):
        '''
        RUN button from the UI has been clicked.
        Tell client to run the current tool config
        '''
        self._run_tool_config()
