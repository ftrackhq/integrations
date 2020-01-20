# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
from collections import OrderedDict

from Qt import QtCore, QtWidgets

class WidgetFactory(object):
    ''''''

    def __init__(self):
        '''
        '''
        super(WidgetFactory, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def create_widget(self, name, schema_fragment, fragment_data=None, parent=None):
        """
            Create the appropriate widget for a given schema element.
        """
        schema_fragment_order = schema_fragment.get('order', [])

        # sort schema fragment keys by the order defined in the schema order
        # any not found entry will be added last.

        if "properties" in schema_fragment:
            schema_fragment_properties = OrderedDict(
                sorted(
                    schema_fragment['properties'].items(),
                    key=lambda pair: schema_fragment_order.index(pair[0])
                    if pair[0] in schema_fragment_order
                    else len(schema_fragment['properties'].keys()) - 1)
            )
            schema_fragment['properties'] = schema_fragment_properties

        if "type" not in schema_fragment:
            return UnsupportedSchema(name, schema_fragment, parent)

        if schema_fragment['type'] == "object":
            return JsonObject(name, schema_fragment, fragment_data, parent)
        elif schema_fragment['type'] == "string":
            return JsonString(name, schema_fragment, fragment_data, parent)
        elif schema_fragment['type'] == "integer":
            return JsonInteger(name, schema_fragment, parent)
        elif schema_fragment['type'] == "array":
            return JsonArray(name, schema_fragment, fragment_data, parent)
        elif schema_fragment['type'] == "number":
            return JsonNumber(name, schema_fragment, parent)
        elif schema_fragment['type'] == "boolean":
            return JsonBoolean(name, schema_fragment, parent)

        return UnsupportedSchema(name, schema_fragment, parent)

class UnsupportedSchema(QtWidgets.QLabel):
    """
        Widget representation of an unsupported schema element.
        Presents a label noting the name of the element and its type.
        If the element is a reference, the reference name is listed
        instead of a type.
    """
    def __init__(self, name, schema_fragment, parent=None):
        self.name = name
        self.fragment = schema_fragment
        self._type = schema_fragment.get("type", schema_fragment.get("$ref",
                                                                     "(?)"))
        QtWidgets.QLabel.__init__(
            self, "(Unsupported schema entry: %s, %s)" % (name, self._type),
            parent)
        self.setStyleSheet("QLabel { font-style: italic; }")

    def to_json_object(self):
        return "(unsupported)"


class JsonObject(QtWidgets.QGroupBox):
    """
        Widget representaiton of an object.
        Objects have properties, each of which is a widget of its own.
        We display these in a groupbox, which on most platforms will
        include a border.
    """
    def __init__(self, name, schema_fragment, fragment_data, parent=None):
        QtWidgets.QGroupBox.__init__(self, name, parent)
        self.widget_factory = WidgetFactory()
        self.name = name
        self.fragment = schema_fragment
        self.vbox = QtWidgets.QVBoxLayout()
        self.innerLayout = QtWidgets.QVBoxLayout()
        #self.vbox.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(self.vbox)
        #self.setFlat(False)
        #self.layout().setContentsMargins(0, 0, 0, 0)
        self.visible_properties = []
        self.fragment_data = fragment_data

        if "title" in self.fragment:
            self.name = self.fragment['title']

        if "description" in self.fragment:
            self.setToolTip(self.fragment['description'])

        if "order" in self.fragment:
            self.visible_properties = self.fragment['order']

        self.properties = {}

        if "properties" not in self.fragment:
            label = QtWidgets.QLabel(
                "Invalid object description (missing properties)",
                self)
            label.setStyleSheet("QLabel { color: red; }")
            self.vbox.addWidget(label)
        else:
            for k, v in self.fragment['properties'].items():
                if k in self.visible_properties:
                    newFragment_data = None
                    if self.fragment_data:
                        newFragment_data = self.fragment_data.get(k)
                    widget = self.widget_factory.create_widget(k, v,
                                                               newFragment_data)
                    self.innerLayout.addWidget(widget)
                    self.properties[k] = widget
        self.vbox.addLayout(self.innerLayout)


    def to_json_object(self):
        out = {}
        for k, v in self.properties.items():
            out[k] = v.to_json_object()
        return out


class JsonString(QtWidgets.QWidget):
    """
        Widget representation of a string.
        Strings are text boxes with labels for names.
    """
    def __init__(self, name, schema_fragment, fragment_data, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.fragment = schema_fragment
        hbox = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(name)
        self.edit = QtWidgets.QLineEdit()
        self.fragment_data = fragment_data

        if "description" in self.fragment:
            self.label.setToolTip(self.fragment['description'])

        if "default" in self.fragment:
            self.edit.setPlaceholderText(self.fragment['default'])

        if self.fragment_data:
            self.edit.setText(self.fragment_data)

        hbox.addWidget(self.label)
        hbox.addWidget(self.edit)

        self.setLayout(hbox)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def to_json_object(self):
        return str(self.edit.text())


class JsonInteger(QtWidgets.QWidget):
    """
        Widget representation of an integer (SpinBox)
    """
    def __init__(self, name, schema_fragment, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.fragment = schema_fragment
        hbox = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(name)
        self.spin  = QtWidgets.QSpinBox()

        if "description" in self.fragment:
            self.label.setToolTip(self.fragment['description'])

        # TODO: min/max

        hbox.addWidget(self.label)
        hbox.addWidget(self.spin)

        self.setLayout(hbox)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def to_json_object(self):
        return self.spin.value()


class JsonNumber(QtWidgets.QWidget):
    """
        Widget representation of a number (DoubleSpinBox)
    """
    def __init__(self, name, schema_fragment, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.fragment = schema_fragment
        hbox = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(name)
        self.spin  = QtWidgets.QDoubleSpinBox()

        if "description" in self.fragment:
            self.label.setToolTip(self.fragment['description'])

        # TODO: min/max

        hbox.addWidget(self.label)
        hbox.addWidget(self.spin)

        self.setLayout(hbox)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def to_json_object(self):
        return self.spin.value()


class JsonArray(QtWidgets.QWidget):
    """
        Widget representation of an array.
        Arrays can contain multiple objects of a type, or
        they can contain objects of specific types.
        We include a label and button for adding types.
    """
    def __init__(self, name, schema_fragment, fragment_data, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.widget_factory = WidgetFactory()
        self.name = name
        self.fragment = schema_fragment
        self.count = 0
        self.vbox = QtWidgets.QVBoxLayout()
        self.fragment_data = fragment_data
        self.maxItems = self.fragment.get('maxItems')

        label = QtWidgets.QLabel(name, self)
        label.setStyleSheet("QLabel { font-weight: bold; }")

        self.vbox.addWidget(label)
        self.innerLayout = QtWidgets.QVBoxLayout()
        if "items" in self.fragment:
            if self.fragment_data:
                for data in self.fragment_data:
                    obj = self.widget_factory.create_widget(
                        self.name, self.fragment['items'], data)
                    self.innerLayout.addWidget(obj)
                    self.count += 1


        self.vbox.addLayout(self.innerLayout)
        self.setLayout(self.vbox)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def click_add(self):
        # TODO: Support array for "items"
        # TODO: Support additionalItems
        if "items" in self.fragment:
            obj = self.widget_factory.create_widget("Item #%d" % (self.count,),
                                                    self.fragment['items'],
                                                    self.schema, self)
            self.count += 1
            self.vbox.addWidget(obj)

    def to_json_object(self):
        out = []
        for i in range(1, self.vbox.count()):
            widget = self.vbox.itemAt(i).widget()
            if "to_json_object" in dir(widget):
                out.append(widget.to_json_object())
        return out


class JsonBoolean(QtWidgets.QCheckBox):
    """
        Widget representing a boolean (CheckBox)
    """
    def __init__(self, name, schema_fragment, parent=None):
        QtWidgets.QCheckBox.__init__(self, name, parent)
        self.name = name
        self.fragment = schema_fragment

        if "description" in self.fragment:
            self.setToolTip(self.fragment['description'])

    def to_json_object(self):
        return bool(self.isChecked())