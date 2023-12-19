# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_qt.dialogs import BaseContextDialog
from ftrack_utils.framework.config.tool import get_plugins, get_groups


class StandardOpenerDialog(BaseContextDialog):
    '''Default Framework Opener dialog'''

    name = 'framework_standard_opener_dialog'
    tool_config_type_filter = ['opener']
    ui_type = 'qt'
    run_button_title = 'OPEN'
    docked = False

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

        super(StandardOpenerDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent,
        )
        self.resize(400, 450)

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

        self.tool_config = None
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
                        try:
                            self.tool_config = tool_config
                        except Exception as error:
                            tool_config_message = error
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
            self._scroll_area_widget.layout().addWidget(label_widget)
            return

        # Build context widgets
        context_plugins = get_plugins(
            self.tool_config, filters={'tags': ['context']}
        )
        for context_plugin in context_plugins:
            if not context_plugin.get('ui'):
                continue
            context_widget = self.init_framework_widget(context_plugin)
            self._scroll_area_widget.layout().addWidget(context_widget)

        # Build component widgets with asset version selector
        component_groups = get_groups(
            self.tool_config, filters={'tags': ['component']}
        )

        for _group in component_groups:
            component_name = _group.get('options').get('component')
            component_label = QtWidgets.QLabel(component_name)
            component_label.setObjectName('h3')
            component_label.setToolTip("Component: {}".format(component_name))
            self._scroll_area_widget.layout().addWidget(component_label)

            collectors = get_plugins(_group, filters={'tags': ['collector']})
            for plugin_config in collectors:
                if not plugin_config.get('ui'):
                    continue
                widget = self.init_framework_widget(plugin_config, _group)

                self._scroll_area_widget.layout().addWidget(widget)

        spacer = QtWidgets.QSpacerItem(
            1,
            1,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding,
        )
        self._scroll_area_widget.layout().addItem(spacer)

    def post_build_ui(self):
        pass
