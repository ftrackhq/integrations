# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from PySide import QtGui


class Workflow(QtGui.QComboBox):
    '''Expose availble workflows from ftrack's server.'''

    def __init__(self, session, parent=None):
        '''Instantiate workflow widget with *session*.'''
        super(Workflow, self).__init__(parent=parent)
        self.session = session
        self._schemas = self.session.query('ProjectSchema').all()
        for schema in self._schemas:
            self.addItem(schema['name'])

    def currentItem(self):
        '''Return the currently selected item.'''
        currentIndex = self.currentIndex()
        return self._schemas[currentIndex]
