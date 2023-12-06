# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore

from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_qt.widgets.accordion import AccordionBaseWidget
from ftrack_utils.framework.config.tool import get_plugins, get_groups
from ftrack_qt.widgets.progress import ProgressWidget


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
        scroll_area_widget_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll_area_widget.setLayout(scroll_area_widget_layout)

        self.tool_widget.layout().addWidget(self._scroll_area, 100)
        self._scroll_area.setWidget(self._scroll_area_widget)

    def build_ui(self):
        # Select the desired tool_config

        self._progress_widget = ProgressWidget()
        self._header.add_widget(self.progress_widget.button_widget)

        if not self.filtered_tool_configs.get("publisher"):
            self.logger.warning("No Publisher tool configs available")
            self._scroll_area_widget.layout().addWidget(
                QtWidgets.QLabel(
                    "<html><i>No Publisher tool configs available</i></html>"
                )
            )
        else:
            self.tool_config = self.filtered_tool_configs.get("publisher")[0]

        self.progress_widget.prepare_add_phases()

        # Build context widgets
        context_plugins = get_plugins(
            self.tool_config, filters={'tags': ['context']}
        )
        for context_plugin in context_plugins:
            self.progress_widget.add_widget(
                'context',
                context_plugin['plugin'],
                phase_label=context_plugin.get('label'),
            )
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
                checkable=not _group.get('optional', False),
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

        spacer = QtWidgets.QSpacerItem(
            1,
            1,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self._scroll_area_widget.layout().addItem(spacer)

        self.progress_widget.phases_added()

    def add_collector_widgets(
        self, collectors, accordion_widget, group_config=None
    ):
        for plugin_config in collectors:
            self.progress_widget.add_widget(
                '{}:collector'.format(
                    group_config.get('options').get('component')
                    if group_config
                    else 'component'
                ),
                plugin_config['plugin'],
                phase_label=plugin_config.get('label'),
            )
            if not plugin_config.get('ui'):
                continue
            widget = self.init_framework_widget(plugin_config, group_config)
            accordion_widget.add_widget(widget)

    def add_validator_widgets(
        self, validators, accordion_widget, group_config=None
    ):
        for plugin_config in validators:
            self.progress_widget.add_widget(
                '{}:validator'.format(
                    group_config.get('options').get('component')
                    if group_config
                    else 'component'
                ),
                plugin_config['plugin'],
                phase_label=plugin_config.get('label'),
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
            self.progress_widget.add_widget(
                '{}:exporter'.format(
                    group_config.get('options').get('component')
                    if group_config
                    else 'component'
                ),
                plugin_config['plugin'],
                phase_label=plugin_config.get('label'),
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
        self.clean_ui()
        self.pre_build_ui()
        self.build_ui()
        self.post_build_ui()
