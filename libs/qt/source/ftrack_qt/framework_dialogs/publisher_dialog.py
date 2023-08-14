# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore


from ftrack_qt.framework_dialogs import VerticalDialogDefinitionBase


class PublisherDialog(VerticalDialogDefinitionBase):
    '''Base Class to represent a Plugin'''

    name = 'framework_publisher_dialog'
    definition_filter = ['publisher']

    def __init__(
            self,
            event_manager,
            client_id,
            connect_methods_callback,
            connect_setter_property_callback,
            connect_getter_property_callback,
            dialog_options,
            parent=None
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
            parent
        )

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
            context_widget_class = context_plugin.widget()
            context_widget = self.init_framework_widget(context_widget_class)
            self.definition_widget.layout().addWidget(context_widget)
        # Build component widgets
        component_steps = definition.get_all(category='step', type='component')
        for step in component_steps:
            #add acordion widget
            # acordion widget add collector
            # accordion widget add validator add exporter
            print(step.name)
        component_plugins = definition.get_all(category='plugin', type='')
        AccordionBaseWidget.SELECT_MODE_NONE,
        AccordionBaseWidget.CHECK_MODE_CHECKBOX
        if checkable
        else AccordionBaseWidget.CHECK_MODE_CHECKBOX_DISABLED,
        checked = checked,
        title = title,
        parent = parent,

        for plugin in self.plugins:
            if plugin.




