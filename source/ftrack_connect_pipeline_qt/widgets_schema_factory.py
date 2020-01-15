# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging

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

    def create_widget(self, name, schema, main_schema, parent=None):
        """
            Create the appropriate widget for a given schema element.
        """

        if "type" not in schema:
            return UnsupportedSchema(name, schema, main_schema, parent)

        if schema['type'] == "object":#checked
            return JsonObject(name, schema, main_schema, parent)
        elif schema['type'] == "string":#checked
            return JsonString(name, schema, main_schema, parent)
        elif schema['type'] == "integer":
            return JsonInteger(name, schema, main_schema, parent)
        elif schema['type'] == "array":#has to be checked
            return JsonArray(name, schema, main_schema, parent)
        elif schema['type'] == "number":
            return JsonNumber(name, schema, main_schema, parent)
        elif schema['type'] == "boolean":
            return JsonBoolean(name, schema, main_schema, parent)

        # TODO: refs
        # TODO: _config misses type
        # TODO: Pattern????

        return UnsupportedSchema(name, schema, main_schema, parent)

#class JsonBaseSchema()

class UnsupportedSchema(QtWidgets.QLabel):
    """
        Widget representation of an unsupported schema element.
        Presents a label noting the name of the element and its type.
        If the element is a reference, the reference name is listed instead of a type.
    """
    def __init__(self, name, schema, main_schema, parent=None):
        self.name = name
        self.schema = schema
        self._type = schema.get("type", schema.get("$ref", "(?)"))
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
    def __init__(self, name, schema, main_schema, parent=None):
        QtWidgets.QGroupBox.__init__(self, name, parent)
        self.widget_factory = WidgetFactory()
        self.name = name
        self.schema = schema
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(self.vbox)
        self.setFlat(False)
        self.main_schema = main_schema

        if "title" in schema:
            self.name = schema['title']

        if "description" in schema:
            self.setToolTip(schema['description'])

        self.properties = {}

        if "properties" not in schema:
            label = QtWidgets.QLabel("Invalid object description (missing properties)", self)
            label.setStyleSheet("QLabel { color: red; }")
            self.vbox.addWidget(label)
        else:
            for k, v in schema['properties'].items():
                #TODO : crate the properties in a sorted order
                widget = self.widget_factory.create_widget(k, v, self.main_schema)
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
    def __init__(self, name, schema, main_schema, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.schema = schema
        hbox = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(name)
        self.edit  = QtWidgets.QLineEdit()
        self.main_schema = main_schema

        if "description" in schema:
            self.label.setToolTip(schema['description'])

        if "default" in schema:
            self.edit.setPlaceholderText(schema['default'])

        hbox.addWidget(self.label)
        hbox.addWidget(self.edit)

        self.setLayout(hbox)

    def to_json_object(self):
        return str(self.edit.text())


class JsonInteger(QtWidgets.QWidget):
    """
        Widget representation of an integer (SpinBox)
    """
    def __init__(self, name, schema, main_schema, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.schema = schema
        hbox = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(name)
        self.spin  = QtWidgets.QSpinBox()
        self.main_schema = main_schema

        if "description" in schema:
            self.label.setToolTip(schema['description'])

        # TODO: min/max

        hbox.addWidget(self.label)
        hbox.addWidget(self.spin)

        self.setLayout(hbox)

    def to_json_object(self):
        return self.spin.value()


class JsonNumber(QtWidgets.QWidget):
    """
        Widget representation of a number (DoubleSpinBox)
    """
    def __init__(self, name, schema, main_schema, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.name = name
        self.schema = schema
        hbox = QtWidgets.QHBoxLayout()

        self.label = QtWidgets.QLabel(name)
        self.spin  = QtWidgets.QDoubleSpinBox()
        self.main_schema = main_schema

        if "description" in schema:
            self.label.setToolTip(schema['description'])

        # TODO: min/max

        hbox.addWidget(self.label)
        hbox.addWidget(self.spin)

        self.setLayout(hbox)

    def to_json_object(self):
        return self.spin.value()


class JsonArray(QtWidgets.QWidget):
    """
        Widget representation of an array.
        Arrays can contain multiple objects of a type, or
        they can contain objects of specific types.
        We include a label and button for adding types.
    """
    def __init__(self, name, schema, main_schema, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.widget_factory = WidgetFactory()
        self.name = name
        self.schema = schema
        self.count = 0
        self.vbox = QtWidgets.QVBoxLayout()

        self.controls = QtWidgets.QHBoxLayout()
        self.main_schema = main_schema

        label = QtWidgets.QLabel(name, self)
        label.setStyleSheet("QLabel { font-weight: bold; }")

        if "description" in schema:
            self.label.setToolTip(schema['description'])
        if "items" in schema:
            for k,v in schema['items'].items():
                if k == "$ref":
                    splitted_values = v.split("/")
                    definition_value = splitted_values[-1]
                    schema = self.main_schema['definitions'][definition_value]
                    obj = self.widget_factory.create_widget(
                        schema['title'], schema,
                        self.main_schema, self)
                    self.count += 1
                    self.vbox.addWidget(obj)
                else:
                    obj = self.widget_factory.create_widget(
                        k, v,
                        self.main_schema, self)
                    self.count += 1
                    self.vbox.addWidget(obj)
            #self.label.setToolTip(schema['items'])
        if "default" in schema:
            self.defaultItems = schema['default']

        #button = QtWidgets.QPushButton("Append Item", self)
        #button.clicked.connect(self.click_add)

        self.controls.addWidget(label)
        #self.controls.addWidget(button)

        self.vbox.addLayout(self.controls)

        self.setLayout(self.vbox)

    def click_add(self):
        # TODO: Support array for "items"
        # TODO: Support additionalItems
        if "items" in self.schema:
            obj = self.widget_factory.create_widget("Item #%d" % (self.count,), self.schema['items'], self.main_schema, self)
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
    def __init__(self, name, schema, main_schema, parent=None):
        QtWidgets.QCheckBox.__init__(self, name, parent)
        self.name = name
        self.schema = schema
        self.main_schema = main_schema

        if "description" in schema:
            self.setToolTip(schema['description'])

    def to_json_object(self):
        return bool(self.isChecked())