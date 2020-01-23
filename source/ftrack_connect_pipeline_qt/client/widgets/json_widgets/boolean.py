# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets


class JsonBoolean(QtWidgets.QCheckBox):
    """
        Widget representing a boolean (CheckBox)
    """
    def __init__(self, name, schema_fragment, fragment_data, previous_object_data,
                 widgetFactory, parent=None):
        QtWidgets.QCheckBox.__init__(self, name, parent)
        self.name = name
        self.fragment = schema_fragment

        if "description" in self.fragment:
            self.setToolTip(self.fragment['description'])

    def to_json_object(self):
        return bool(self.isChecked())