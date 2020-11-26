# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.schema import BaseJsonWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import AccordionWidget


class ComponentsArray(BaseJsonWidget):
    '''
    Override widget representation of an array
    '''

    @property
    def accordion_widgets(self):
        return self._accordion_widgets

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise ComponentsArray with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(ComponentsArray, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )

    def build(self):
        self._accordion_widgets = []

        if 'items' in self.schema_fragment and self.fragment_data:
            for data in self.fragment_data:
                if type(data) == dict:
                    name = data.get('name')
                else:
                    name = data
                optional_component = False
                for package in self.widget_factory.package['components']:
                    if package['name'] == name:
                        optional_component = data.get('optional', False)
                        break

                accordion_widget = AccordionWidget(
                    title=name, checkable=optional_component
                )
                obj = self.widget_factory.create_widget(
                    name, self.schema_fragment['items'], data,
                    self.previous_object_data
                )
                accordion_widget.add_widget(obj)

                self.layout().addWidget(accordion_widget)
                self._accordion_widgets.append(accordion_widget)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def to_json_object(self):
        out = []
        for accordion_widget in self._accordion_widgets:
            for idx in range(0, accordion_widget.count_widgets()):
                widget = accordion_widget.get_witget_at(idx)
                if 'to_json_object' in dir(widget):
                    data = widget.to_json_object()
                    data['enabled'] = accordion_widget.is_checked()
                    out.append(data)
        return out