# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets


class JsonInteger(QtWidgets.QWidget):
    """
        Widget representation of an integer (SpinBox)
    """
    def __init__(self, name, schema_fragment, fragment_data, plugin_type,
                 widgetFactory, parent=None):
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