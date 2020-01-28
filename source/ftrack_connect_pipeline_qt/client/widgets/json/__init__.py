# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets


class BaseJsonWidget(QtWidgets.QWidget):
    '''
    Base class of a widget representation from json schema types
    '''
    def __init__(
            self, name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=None
    ):
        '''Initialise BaseJsonWidget with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*

        *name* widget name

        *schema_fragment* fragment of the schema to generate the current widget

        *fragment_data* fragment of the data from the definition to fill
        the current widget.

        *previous_object_data* fragment of the data from the previous schema
        fragment

        *widget_factory* should be the
        :class:`ftrack_connect_pipeline_qt.client.widgets.json.factory.WidgetFactory`
        instance to use for recursive generation of json widgets.

        *parent* widget to parent the current widget (optional).

        '''
        super(BaseJsonWidget, self).__init__(parent=parent)

        # setup default vars
        self.widget_factory = widget_factory
        self.schema_fragment = schema_fragment
        self.fragment_data = fragment_data
        self.previous_object_data = previous_object_data
        self._parent = parent

        # checks
        self.properties_order = self.schema_fragment.get('order', [])
        self.name = name
        self.description = self.schema_fragment.get('description')
        self.properties = self.schema_fragment.get('properties', {})
        self._type = self.schema_fragment.get('type')
        self.required_keys = self.schema_fragment.get('required', [])

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''pre build function, mostly used setup the widget's layout.'''
        # add default layout
        self.v_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.v_layout)

    def build(self):
        '''build function , mostly used to create the widgets.'''
        pass

    def post_build(self):
        '''post build function , mostly used connect widgets events.'''
        pass

    def to_json_object(self):
        '''Return a formated json with the data from the current widget'''
        return {}


from ftrack_connect_pipeline_qt.client.widgets.json.array import JsonArray
from ftrack_connect_pipeline_qt.client.widgets.json.boolean import JsonBoolean
from ftrack_connect_pipeline_qt.client.widgets.json.integer import JsonInteger
from ftrack_connect_pipeline_qt.client.widgets.json.number import JsonNumber
from ftrack_connect_pipeline_qt.client.widgets.json.object import JsonObject
from ftrack_connect_pipeline_qt.client.widgets.json.string import JsonString
from ftrack_connect_pipeline_qt.client.widgets.json.unsupported import UnsupportedSchema