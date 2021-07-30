# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from Qt import QtGui, QtCore, QtWidgets

# TODO: Not sure to inherit from object or widget, is now object to avoid
#  creating to many widgets
class BaseUIWidget(object):
    '''
    Base class of a widget representation from json schema types
    '''

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        '''Sets asset type from the given *value*'''
        self._name = value

    @property
    def id(self):
        return self._id

    @property
    def widget(self):
        return self._widget

    def __init__(
            self, name, fragment_data, parent=None
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
        super(BaseUIWidget, self).__init__()
        # setup default vars
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        # self.widget_factory = widget_factory
        # self.schema_fragment = schema_fragment
        self.fragment_data = fragment_data
        self._parent = parent

        # checks
        # self.properties_order = self.schema_fragment.get('order', [])
        self.name = name
        # self.description = self.schema_fragment.get('description')
        # self.properties = self.schema_fragment.get('properties', {})
        # self._type = self.schema_fragment.get('type')
        # self.required_keys = self.schema_fragment.get('required', [])
        self._widget = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''pre build function, mostly used setup the widget's layout.'''
        pass
        # self.v_layout = QtWidgets.QVBoxLayout()
        # self.setLayout(self.v_layout)
        # self.layout().setContentsMargins(0, 0, 0, 0)
        # self.layout().setSpacing(5)

    def build(self):
        '''build function , mostly used to create the widgets.'''
        pass

    def post_build(self):
        '''post build function , mostly used connect widgets events.'''
        pass

    def parent_widget(self, widget):
        if self.widget:
            if hasattr(widget, 'widget'):
                self.widget.layout().addWidget(widget.widget)
            else:
                self.widget.layout().addWidget(widget)
        else:
            self.logger.error("Please create a widget before parent")

    def to_json_object(self):
        '''Return a formated json with the data from the current widget'''
        return {}