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

    def create_widget(self, name, schema_fragment, properties_order=None, parent=None):
        """
            Create the appropriate widget for a given schema element.
        """
        properties_order = properties_order or []

        # sort schema fragment keys by the order defined in the schema order
        # any not found entry will be added last.
        # schema_fragment = OrderedDict(
        #     sorted(
        #         schema_fragment.items(),
        #         key=lambda pair: schema_fragment_order.index(pair[0])
        #         if pair[0] in schema_fragment_order
        #         else len(schema_fragment.keys()) -1)
        # )

        if "type" not in schema_fragment:
            return UnsupportedSchema(name, schema_fragment, properties_order, parent)

        if schema_fragment['type'] == "object":
            return JsonObject(name, schema_fragment, properties_order, parent)
        elif schema_fragment['type'] == "string":
            return JsonString(name, schema_fragment, properties_order, parent)
        elif schema_fragment['type'] == "integer":
            return JsonInteger(name, schema_fragment, properties_order, parent)
        elif schema_fragment['type'] == "array":
            return JsonArray(name, schema_fragment, properties_order, parent)
        elif schema_fragment['type'] == "number":
            return JsonNumber(name, schema_fragment, properties_order, parent)
        elif schema_fragment['type'] == "boolean":
            return JsonBoolean(name, schema_fragment, properties_order, parent)

        # TODO: refs
        # TODO: _config misses type
        # TODO: Pattern????

        return UnsupportedSchema(name, schema_fragment, properties_order, parent)

#class JsonBaseSchema()

class UnsupportedSchema(QtWidgets.QLabel):
    """
        Widget representation of an unsupported schema element.
        Presents a label noting the name of the element and its type.
        If the element is a reference, the reference name is listed instead of a type.
    """
    def __init__(self, name, schema_fragment, schema, parent=None):
        self.name = name
        self.fragment = schema_fragment
        self._type = schema_fragment.get("type", schema_fragment.get("$ref", "(?)"))
        QtWidgets.QLabel.__init__(self, "(Unsupported schema entry: %s, %s)" % (name, self._type), parent)
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
    def __init__(self, name, schema_fragment, properties_order, parent=None):
        QtWidgets.QGroupBox.__init__(self, name, parent)
        self.widget_factory = WidgetFactory()
        self.name = name
        self.fragment = schema_fragment
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(self.vbox)
        self.setFlat(False)
        self.properties_order = properties_order
        self.layout().setContentsMargins(0, 0, 0, 0)

        if "title" in self.fragment:
            self.name = self.fragment['title']

        if "description" in self.fragment:
            self.setToolTip(self.fragment['description'])

        self.properties = {}

        if "properties" not in self.fragment:
            label = QtWidgets.QLabel("Invalid object description (missing properties)", self)
            label.setStyleSheet("QLabel { color: red; }")
            self.vbox.addWidget(label)
        else:
            if self.properties_order:
                for property_name in self.properties_order:
                    new_properties_order = self.fragment['properties'][property_name].get('order', [])
                    widget = self.widget_factory.create_widget(
                        property_name,
                        self.fragment['properties'][property_name],
                        properties_order = new_properties_order)
                    self.vbox.addWidget(widget)
                    self.properties[property_name] = widget
            else:
                for k, v in self.fragment['properties'].items():
                    new_properties_order = v.get('order', [])
                    widget = self.widget_factory.create_widget(k, v, new_properties_order)
                    self.vbox.addWidget(widget)
                    self.properties[k] = widget


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
    def __init__(self, name, schema_fragment, properties_order, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.fragment = schema_fragment
        hbox = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(name)
        self.edit  = QtWidgets.QLineEdit()
        self.properties_order = properties_order

        if "description" in self.fragment:
            self.label.setToolTip(self.fragment['description'])

        if "default" in self.fragment:
            self.edit.setPlaceholderText(self.fragment['default'])

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
    def __init__(self, name, schema_fragment, properties_order, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.fragment = schema_fragment
        hbox = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(name)
        self.spin  = QtWidgets.QSpinBox()
        self.properties_order = properties_order

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
    def __init__(self, name, schema_fragment, properties_order, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.fragment = schema_fragment
        hbox = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(name)
        self.spin  = QtWidgets.QDoubleSpinBox()
        self.properties_order = properties_order

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
    def __init__(self, name, schema_fragment, properties_order, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.widget_factory = WidgetFactory()
        self.name = name
        self.fragment = schema_fragment
        self.count = 0
        self.vbox = QtWidgets.QVBoxLayout()

        self.controls = QtWidgets.QHBoxLayout()
        self.properties_order = properties_order

        label = QtWidgets.QLabel(name, self)
        label.setStyleSheet("QLabel { font-weight: bold; }")

        if "description" in self.fragment:
            self.label.setToolTip(self.fragment['description'])
        if "items" in self.fragment:
            new_properties_order = self.fragment['items'].get('order', [])
            obj = self.widget_factory.create_widget(
                self.name, self.fragment['items'],
                properties_order=new_properties_order,
                parent=self)
            self.count += 1
            self.vbox.addWidget(obj)
            #self.label.setToolTip(schema['items'])
        if "default" in self.fragment:
            self.defaultItems = self.fragment['default']

        #button = QtWidgets.QPushButton("Append Item", self)
        #button.clicked.connect(self.click_add)

        self.controls.addWidget(label)
        #self.controls.addWidget(button)

        self.vbox.addLayout(self.controls)

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
    def __init__(self, name, schema_fragment, properties_order, parent=None):
        QtWidgets.QCheckBox.__init__(self, name, parent)
        self.name = name
        self.fragment = schema_fragment
        self.properties_order = properties_order

        if "description" in self.fragment:
            self.setToolTip(self.fragment['description'])

    def to_json_object(self):
        return bool(self.isChecked())