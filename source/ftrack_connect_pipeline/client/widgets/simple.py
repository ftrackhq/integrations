# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from QtExt import QtWidgets, QtCore
from ftrack_connect_pipeline.client.widgets import BaseWidget


class SimpleWidget(BaseWidget):

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        self._type_mapping = {
            str: self._build_str_widget,
            int: self._build_int_widget,
            float: self._build_float_widget,
            list: self._build_list_widget,
        }
        super(SimpleWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options)

    def _build_str_widget(self, value):
        return QtWidgets.QLineEdit(str(value))

    def _build_int_widget(self, value):
        return QtWidgets.QSpinBox(int(value))

    def _build_float_widget(self, value):
        return QtWidgets.QDoubleSpinBox(float(value))

    def _build_list_widget(self, values):
        widget = QtWidgets.QListWidget()
        widget.addItems(values)
        return widget

    def build(self):
        super(SimpleWidget, self).build()

        for key, value in self.options.items():
            self._simple_option_layout = QtWidgets.QHBoxLayout()
            self._simple_option_layout.setContentsMargins(5, 1, 5, 1)
            self._simple_option_layout.setAlignment(QtCore.Qt.AlignTop)

            label = QtWidgets.QLabel(key)

            value_type = type(value)
            widget_object = self._type_mapping.get(value_type, self._build_str_widget)
            widget = widget_object(value)

            self.add_widget(key, widget)

            self._simple_option_layout.addWidget(label)
            self.layout().addLayout(self._simple_option_layout)

    def post_build(self):
        for widget_name, widget in self.widgets.items():
            self._simple_option_layout.addWidget(widget)

    def value(self):
        result = {}
        for label, widget in self.widgets.items():
            result[label] = widget.text()

        return result