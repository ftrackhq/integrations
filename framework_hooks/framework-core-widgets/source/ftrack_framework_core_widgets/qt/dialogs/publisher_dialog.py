# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtCore

from ftrack_framework_core_widgets.qt.dialogs.vertical_dialog_definition_base import (
    VerticalDialogDefinitionBase,
)
from ftrack_qt.widgets.accordion import AccordionBaseWidget
from ftrack_qt.ui import theme

# TODO: review and docstring this code
class PublisherDialog(VerticalDialogDefinitionBase):
    '''Base Class to represent a Plugin'''

    name = 'framework_publisher_dialog'
    definition_filter = ['publisher']
    ui_type = 'qt'
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
        Initialise BasePlugin with instance of
        :class:`ftrack_api.session.Session`
        '''

        super(PublisherDialog, self).__init__(
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent,
        )
        # Apply theme and with DCC specific properties
        theme.applyTheme(self, self.theme)
        self.setProperty('background', self.style)
        self.setProperty('docked', 'true' if self.docked else 'false')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

    # TODO: this should be an ABC
    def pre_build(self):
        super(PublisherDialog, self).pre_build()

    # TODO: this should be an ABC
    def build(self):
        super(PublisherDialog, self).build()

    # TODO: this should be an ABC
    def post_build(self):
        super(PublisherDialog, self).post_build()

    def build_definition_ui(self, definition):
        # Build context widgets
        context_plugins = definition.get_all(category='plugin', type='context')
        for context_plugin in context_plugins:
            if not context_plugin.widget:
                continue
            context_widget = self.init_framework_widget(context_plugin)
            self.definition_widget.layout().addWidget(context_widget)
        # Build component widgets
        component_steps = definition.get_all(category='step', type='component')
        for step in component_steps:
            # TODO: add a key visible in the definition to hide the step if wanted.
            step_accordion_widget = AccordionBaseWidget(
                selectable=False,
                show_checkbox=True,
                checkable=not step.optional,
                title=step.name,
                selected=False,
                checked=step.enabled,
                collapsable=True,
                collapsed=True,
            )
            step_plugins = step.get_all(category='plugin')
            for step_plugin in step_plugins:
                if not step_plugin.widget:
                    continue
                widget = self.init_framework_widget(step_plugin)
                if step_plugin.type == 'collector':
                    step_accordion_widget.add_widget(widget)
                if step_plugin.type == 'validator':
                    step_accordion_widget.add_option_widget(
                        widget, section_name='Validators'
                    )
                if step_plugin.type == 'exporter':
                    step_accordion_widget.add_option_widget(
                        widget, section_name='Exporters'
                    )
            self._definition_widget.layout().addWidget(step_accordion_widget)
