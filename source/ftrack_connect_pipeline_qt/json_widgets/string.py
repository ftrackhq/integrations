# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets


class JsonString(QtWidgets.QWidget):
    """
        Widget representation of a string.
        Strings are text boxes with labels for names.
    """
    def __init__(self, name, schema_fragment, fragment_data, parent_data,
                 widgetFactory, parent=None):
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