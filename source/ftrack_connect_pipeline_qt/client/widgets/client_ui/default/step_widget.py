# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from ftrack_connect_pipeline_qt.client.widgets.client_ui import BaseUIWidget
from Qt import QtGui, QtCore, QtWidgets


class DefaultStepWidget(BaseUIWidget):
    '''Widget representation of a boolean'''

    @property
    def is_enabled(self):
        return self.check_box.isChecked()


    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        super(DefaultStepWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def pre_build(self):
        self._is_optional = self.fragment_data.get('optional')

    def build(self):
        self._widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        self.widget.setLayout(main_layout)

        self.check_box = QtWidgets.QCheckBox(self.name)
        self.widget.layout().addWidget(self.check_box)
        if not self.is_optional:
            self.check_box.setChecked(True)
            self.check_box.setEnabled(False)

    def post_build(self):
        super(DefaultStepWidget, self).post_build()

    def set_unavailable(self):
        self.check_box.setChecked(False)
        self.widget.setEnabled(False)

    def set_available(self):
        self.check_box.setChecked(True)
        self.widget.setEnabled(True)
        if not self.is_optional:
            self.check_box.setEnabled(False)
        else:
            self.check_box.setEnabled(True)

    def to_json_object(self):
        '''Return a formated json with the data from the current widget'''
        out = {}
        out['enabled'] = self.is_enabled
        return out
