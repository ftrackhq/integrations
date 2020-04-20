# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.schema import BaseJsonWidget
from ftrack_connect_pipeline_qt.ui.utility.widget.accordion import AccordionWidget


class ComponentsArray(BaseJsonWidget):
    '''
    Override widget representation of an array
    '''

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

        if 'items' in self.schema_fragment and self.fragment_data:
            for data in self.fragment_data:
                if type(data) == dict:
                    name = data.get('name')
                else:
                    name = data
                self._accordion = AccordionWidget(title=name)
                obj = self.widget_factory.create_widget(
                    name, self.schema_fragment['items'], data,
                    self.previous_object_data
                )
                self._accordion.add_widget(obj)

                self.layout().addWidget(self._accordion)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def to_json_object(self):
        out = []
        for idx in range(0, self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(idx)
            for i in range(0, tab_widget.layout().count()):
                widget = tab_widget.layout().itemAt(i).widget()
                if 'to_json_object' in dir(widget):
                    out.append(widget.to_json_object())
        return out