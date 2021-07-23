# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


from Qt import QtGui, QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.schema import JsonObject
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import AccordionWidget


class PluginContainerObject(JsonObject):
    '''
    Override widget representation of an object
    '''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise PluginContainerObject with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(PluginContainerObject, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    def build(self):
        if self.previous_object_data:
            self.stage_name = self.previous_object_data.get('name')

        self.properties_widgets = {}

        if not self.properties:
            label = QtWidgets.QLabel(
                'Invalid object description (missing properties)',
                self)
            label.setStyleSheet('QLabel { color: red; }')
            self.layout().addWidget(label)
        else:
            if 'widget' in list(self.properties.keys()):
                widget = self.widget_factory.fetch_plugin_widget(
                    self.fragment_data, self.stage_name
                )
                self.layout().addWidget(widget)
            else:
                for k, v in list(self.properties.items()):
                    new_fragment_data = None
                    if self.fragment_data:
                        new_fragment_data = self.fragment_data.get(k)
                    widget = self.widget_factory.create_widget(
                        k, v, new_fragment_data, self.fragment_data
                    )
                    self.layout().addWidget(widget)
                    self.properties_widgets[k] = widget

class PluginContainerAccordionObject(JsonObject):
    '''
    Override widget representation of an object
    '''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise PluginContainerObject with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(PluginContainerAccordionObject, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    def build(self):
        if self.previous_object_data:
            self.stage_name = self.previous_object_data.get('name')

        self.properties_widgets = {}

        if not self.properties:
            label = QtWidgets.QLabel(
                'Invalid object description (missing properties)',
                self)
            label.setStyleSheet('QLabel { color: red; }')
            self.layout().addWidget(label)
        else:
            if 'widget' in list(self.properties.keys()):
                widget = self.widget_factory.fetch_plugin_widget(
                    self.fragment_data, self.stage_name
                )
                accordion_widget = AccordionWidget(
                    title=self.name, checkable=False
                )
                accordion_widget.add_widget(widget)
                self.layout().addWidget(accordion_widget)
            else:
                for k, v in list(self.properties.items()):
                    new_fragment_data = None
                    if self.fragment_data:
                        new_fragment_data = self.fragment_data.get(k)
                    widget = self.widget_factory.create_widget(
                        k, v, new_fragment_data, self.fragment_data
                    )
                    self.layout().addWidget(widget)
                    self.properties_widgets[k] = widget

    def to_json_object(self):
        out = {}

        if self.schema_fragment.get('allOf'):
            # return the widget information when schema cointains allOf,
            # the widget doesn't have any inner widgets, so we query the
            # information from the widget 0 which is the allOf widget, and
            # augment the widget information with the data_fragment keys and
            # values to match the schema.
            widget = self.layout().itemAt(0).widget()
            if 'to_json_object' in dir(widget):
                out = widget.to_json_object()
                for k, v in list(self.fragment_data.items()):
                    if k not in list(out.keys()):
                        out[k] = v
        elif 'widget' in list(self.properties.keys()):
            # return the widget information when widget is in properties keys,
            # and augment the widget information with the data_fragment keys and
            # values to match the schema.
            widget = self.widget_factory.get_registered_widget_plugin(
                self.fragment_data)
            if widget.__class__.__name__ == 'AccordionWidget':
                for idx in range(0, widget.count_widgets()):
                    widget = widget.get_witget_at(idx)
                    if 'to_json_object' in dir(widget):
                        data = widget.to_json_object()
                        data['enabled'] = widget.is_checked()
                        for k, v in list(self.fragment_data.items()):
                            if k not in list(data.keys()):
                                out[k] = v
            else:
                out = widget.to_json_object()
                for k, v in list(self.fragment_data.items()):
                    if k not in list(out.keys()):
                        out[k] = v
        else:
            # Return the widget information for any other case.
            for k, v in list(self.properties.items()):
                widget = self.properties_widgets[k]
                out[k] = widget.to_json_object()

        return out
