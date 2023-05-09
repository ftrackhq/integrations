# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from Qt import QtWidgets

from ftrack_connect_pipeline_qt.ui.factory.base import BaseUIWidgetObject


class DefaultStepWidgetObject(BaseUIWidgetObject):
    '''Widget representation of a schema step'''

    @property
    def enabled(self):
        '''(Redefine) Return True if widget is enabled as evaluated from schema'''
        return self.check_box.isChecked()

    @enabled.setter
    def enabled(self, value):
        '''(Redefine) Set widget enable property'''
        self.check_box.setChecked(value)

    @property
    def available(self):
        '''Return true if widget is available'''
        return self.widget.isEnabled()

    @available.setter
    def available(self, value):
        '''Set widget available property to *value*'''
        if value:
            self.enabled = True
            self.widget.setEnabled(True)
            if not self.optional:
                self.check_box.setEnabled(False)
            else:
                self.check_box.setEnabled(True)
        else:
            self.enabled = False
            self.widget.setEnabled(False)

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise DefaultStepWidgetObject with *name*,
        *fragment_data* and *parent*'''

        super(DefaultStepWidgetObject, self).__init__(
            name, fragment_data, parent=parent
        )
        self._component = None

    def pre_build(self):
        self._is_optional = self.fragment_data.get('optional')
        self._widget = QtWidgets.QWidget()
        self.widget.setLayout(QtWidgets.QVBoxLayout())

    def build(self):
        self.check_box = QtWidgets.QCheckBox(self.name)
        self.widget.layout().addWidget(self.check_box)
        if not self.optional:
            self.check_box.setChecked(True)
            self.check_box.setEnabled(False)
        self.check_box.hide()

    def post_build(self):
        super(DefaultStepWidgetObject, self).post_build()

    def check_components(self, session, components):
        '''Set available property based on *components*'''
        self._component = None
        self._session = session
        for component in components:
            if component['name'] == self.name:
                self._component = component
                break
        if not self._component:
            self.available = False
        else:
            self.available = True

    def to_json_object(self):
        '''(Override)'''
        out = {}
        out['enabled'] = self.enabled
        return out
