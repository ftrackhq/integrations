# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets


class UnsupportedSchema(QtWidgets.QLabel):
    """
        Widget representation of an unsupported schema element.
        Presents a label noting the name of the element and its type.
        If the element is a reference, the reference name is listed
        instead of a type.
    """
    def __init__(self, name, schema_fragment, fragment_data, previous_object_data,
                 widgetFactory, parent=None):
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