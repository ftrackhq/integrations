# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from functools import partial
from qtpy import QtWidgets, QtCore
from ftrack_connect_pipeline.client.widgets import BaseWidget


class SimpleWidget(BaseWidget):

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        self._type_mapping = {
            str: self._build_str_widget,
            int: self._build_int_widget,
            float: self._build_float_widget,
            list: self._build_list_widget,
            bool: self._build_bool_widget
        }
        super(SimpleWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options)

    def _register_widget(self, name, widget):
        '''Register *widget* with *name* and add it to main layout.'''
        widget_layout = QtWidgets.QHBoxLayout()
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.setAlignment(QtCore.Qt.AlignTop)
        label = QtWidgets.QLabel(name)

        widget_layout.addWidget(label)
        widget_layout.addWidget(widget)
        self.layout().addLayout(widget_layout)

    def _build_str_widget(self, key, value):
        '''build a string widget out of options *key* and *value* '''
        widget = QtWidgets.QLineEdit(str(value))
        self._register_widget(key, widget)
        update_fn = partial(self.set_option_result, key=key)
        widget.textChanged.connect(update_fn)
        self.set_option_result(value, key)

    def _build_int_widget(self, key, value):
        '''build an integer widget out of options *key* and *value* '''
        widget = QtWidgets.QSpinBox()
        widget.setValue(value)
        self._register_widget(key, widget)
        update_fn = partial(self.set_option_result, key=key)
        widget.valueChanged.connect(update_fn)
        self.set_option_result(value, key)

    def _build_float_widget(self, key, value):
        '''build a float widget out of options *key* and *value* '''
        widget= QtWidgets.QDoubleSpinBox()
        widget.setValue(value)
        self._register_widget(key, widget)
        update_fn = partial(self.set_option_result, key=key)
        widget.valueChanged.connect(update_fn)
        self.set_option_result(value, key)

    def _build_bool_widget(self, key, value):
        '''build a float widget out of options *key* and *value* '''
        widget= QtWidgets.QCheckBox()
        widget.setTristate(False)
        widget.setCheckState(QtCore.Qt.CheckState(value))
        self._register_widget(key, widget)
        update_fn = partial(self.set_option_result, key=key)
        widget.stateChanged.connect(update_fn)
        self.set_option_result(value, key)

    def _build_list_widget(self, key, values):
        '''build a list widget out of options *key* and *values* '''
        widget = QtWidgets.QComboBox()
        widget.addItems(values)
        self._register_widget(key, widget)
        update_fn = partial(self.set_option_result, key=key)
        widget.editTextChanged.connect(update_fn)
        if len(values) > 0:
            self.set_option_result(values[0], key)

    def build(self):
        super(SimpleWidget, self).build()

        for key, value in self.options.items():
            value_type = type(value)
            widget_fn = self._type_mapping.get(value_type, self._build_str_widget)
            widget_fn(key, value)
