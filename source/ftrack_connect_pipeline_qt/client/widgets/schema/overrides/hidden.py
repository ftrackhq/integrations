# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from ftrack_connect_pipeline_qt.client.widgets.schema import (
    JsonObject, JsonString, JsonBoolean, JsonArray
)
from ftrack_connect_pipeline_qt.client.widgets.schema.overrides.step import (
    StepArray
)
from Qt import QtCore, QtWidgets


class HiddenBoolean(JsonBoolean):
    '''
    Override widget representation of a boolean field
    '''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise HiddenBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(HiddenBoolean, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )
        self.setVisible(False)


def merge(source, destination):
    """
    Utility function to merge two json objects
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination

class HiddenObject(JsonObject):
    '''
    Override widget representation of an object
    '''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise HiddenObject with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(HiddenObject, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )
        #self.setVisible(False)

    def create_inner_widget(self, name, parent):
        widget = QtWidgets.QWidget(parent)
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        widget.setLayout(layout)
        widget.layout().setContentsMargins(0, 0, 0, 0)
        return widget


class HiddenString(JsonString):
    '''
    Override widget representation of a string
    '''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise HiddenString with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(HiddenString, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )
        self.setVisible(False)

class HiddenArray(JsonArray):
    '''
    Override widget representation of an object
    '''

    def __init__(
            self, name, schema_fragment, fragment_data,
            previous_object_data, widget_factory, parent=None
    ):
        '''Initialise HiddenArray with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(HiddenArray, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widget_factory, parent=parent
        )
        self.setVisible(False)
