# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from Qt import QtWidgets

from ftrack_connect_pipeline_qt.ui.client import BaseUIWidget


class DefaultStepWidget(BaseUIWidget):
    '''Widget representation of a boolean'''

    @property
    def is_enabled(self):
        return self.check_box.isChecked()

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''

        super(DefaultStepWidget, self).__init__(name, fragment_data, parent=parent)

        self._component = None

    def pre_build(self):
        self._is_optional = self.fragment_data.get('optional')
        self._widget = QtWidgets.QWidget()
        self.widget.setLayout(QtWidgets.QVBoxLayout())

    def build(self):
        self.check_box = QtWidgets.QCheckBox(self.name)
        self.widget.layout().addWidget(self.check_box)
        if not self.is_optional:
            self.check_box.setChecked(True)
            self.check_box.setEnabled(False)
        self.check_box.hide()

    def post_build(self):
        super(DefaultStepWidget, self).post_build()

    def check_components(self, session, components):
        self._component = None
        self._session = session
        for component in components:
            if component['name'] == self.name:
                self._component = component
                break
        if not self._component:
            self.set_unavailable()
        else:
            self.set_available()

    def set_unavailable(self):
        self.check_box.setChecked(False)
        self.widget.setEnabled(False)
        self.set_enabled(False)

    def set_available(self):
        self.widget.setEnabled(True)
        self.set_enabled(True)
        self.check_box.setChecked(True)
        if not self.is_optional:
            self.check_box.setEnabled(False)
        else:
            self.check_box.setEnabled(True)

    def to_json_object(self):
        '''Return a formated json with the data from the current widget'''
        out = {}
        out['enabled'] = self.is_enabled
        return out
