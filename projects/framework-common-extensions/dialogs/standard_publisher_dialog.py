# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

import ftrack_constants.framework as constants
from ftrack_utils.framework.config.tool import get_plugins, get_groups
from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_qt.widgets.accordion import AccordionBaseWidget
from ftrack_qt.widgets.progress import ProgressWidget


class StandardPublisherDialog(BaseContextDialog):
    '''Default Framework Publisher dialog'''

    name = 'framework_standard_publisher_dialog'
    tool_config_type_filter = ['publisher']
    ui_type = 'qt'
    run_button_title = 'PUBLISH'
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
        # TODO: Reset this when re-selecting tool config
        self._init_progress_widget = True

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
        scroll_area_widget_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll_area_widget.setLayout(scroll_area_widget_layout)

        self.tool_widget.layout().addWidget(self._scroll_area, 100)
        self._scroll_area.setWidget(self._scroll_area_widget)

    def build_ui(self):
        # Create progress widget, keep it if already exists
        if self._init_progress_widget:
            self.progress_widget = ProgressWidget()
            self.header.add_widget(self.progress_widget.button_widget)
            self.progress_widget.prepare_add_phases()
        # Select the desired tool_config

        self.tool_config = None

        if self.filtered_tool_configs.get("publisher"):
            if 'tool-config-filter' in self.dialog_options:
                tool_config_filter = self.dialog_options['tool-config-filter']
                for tool_config in self.filtered_tool_configs["publisher"]:
                    if (
                        tool_config.get('name', '')
                        .lower()
                        .find(tool_config_filter.lower())
                        > -1
                    ):
                        self.tool_config = tool_config
                        break
            else:
                self.tool_config = self.filtered_tool_configs["publisher"][0]

        if not self.tool_config:
            self.logger.warning(
                f'No Publisher tool configs available (filter:'
                f' {self.dialog_options.get("tool-config-filter")})'
            )

            self._scroll_area_widget.layout().addWidget(
                QtWidgets.QLabel(
                    '<html><i>No Publisher tool configs available</i></html>'
                )
            )

        processed_plugins = []

        # Build context widgets
        context_plugins = get_plugins(
            self.tool_config, filters={'tags': ['context']}
        )
        for context_plugin in context_plugins:
            if self._init_progress_widget:
                self.progress_widget.add_phase_widget(
                    context_plugin['reference'],
                    'context',
                    context_plugin.get('label')
                    or context_plugin['plugin'].replace('_', ' ').title(),
                )
                processed_plugins.append(context_plugin['reference'])
            if not context_plugin.get('ui'):
                continue
            context_widget = self.init_framework_widget(context_plugin)
            self._scroll_area_widget.layout().addWidget(context_widget)

        # Build component widgets
        component_groups = get_groups(
            self.tool_config, filters={'tags': ['component']}
        )

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

            self._scroll_area_widget.layout().addWidget(group_accordion_widget)
            if self._init_progress_widget:
                processed_plugins.extend(
                    [plugin['reference'] for plugin in get_plugins(_group)]
                )

        if self._init_progress_widget:
            # Add additional unprocessed plugins to progress widget
            for plugin_config in get_plugins(self.tool_config):
                if not self.progress_widget.has_phase_widget(
                    plugin_config['reference']
                ):
                    if plugin_config['reference'] in processed_plugins:
                        continue
                    self.progress_widget.add_phase_widget(
                        plugin_config['reference'],
                        'finalizers',
                        plugin_config.get('label')
                        or plugin_config['plugin'].replace('_', ' ').title(),
                    )
            # Wrap progress widget
            self.progress_widget.phases_added()
            self._init_progress_widget = False

        spacer = QtWidgets.QSpacerItem(
            1,
            1,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self._scroll_area_widget.layout().addItem(spacer)

    def add_collector_widgets(
        self, collectors, accordion_widget, group_config=None
    ):
        for plugin_config in collectors:
            if self._init_progress_widget:
                self.progress_widget.add_phase_widget(
                    plugin_config['reference'],
                    '{}:collector'.format(
                        group_config.get('options').get('component')
                        if group_config
                        else 'component'
                    ),
                    plugin_config.get('label')
                    or plugin_config['plugin'].replace('_', ' ').title(),
                )
            if not plugin_config.get('ui'):
                continue
            widget = self.init_framework_widget(plugin_config, group_config)
            accordion_widget.add_widget(widget)

    def add_validator_widgets(
        self, validators, accordion_widget, group_config=None
    ):
        for plugin_config in validators:
            if self._init_progress_widget:
                self.progress_widget.add_phase_widget(
                    plugin_config['reference'],
                    '{}:validator'.format(
                        group_config.get('options').get('component')
                        if group_config
                        else 'component'
                    ),
                    plugin_config.get('label')
                    or plugin_config['plugin'].replace('_', ' ').title(),
                )
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
            if self._init_progress_widget:
                self.progress_widget.add_phase_widget(
                    plugin_config['reference'],
                    '{}:exporter'.format(
                        group_config.get('options').get('component')
                        if group_config
                        else 'component'
                    ),
                    plugin_config.get('label')
                    or plugin_config['plugin'].replace('_', ' ').title(),
                )
            if not plugin_config.get('ui'):
                continue
            widget = self.init_framework_widget(plugin_config, group_config)
            accordion_widget.add_option_widget(
                widget, section_name='Exporters'
            )

    def post_build_ui(self):
        pass

    def _on_run_button_clicked(self):
        '''(Override) Refresh context widget(s) upon publish'''
        super(StandardPublisherDialog, self)._on_run_button_clicked()
        if self.progress_widget.status == constants.status.SUCCESS_STATUS:
            self.clean_ui()
            self.pre_build_ui()
            self.build_ui()
            self.post_build_ui()
