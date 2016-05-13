# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from PySide import QtGui
import logging


class Workflow(QtGui.QComboBox):
    '''Expose availble workflows from ftrack's server.'''

    def __init__(self, session, parent=None):
        '''Instantiate workflow widget with *session*.'''
        super(Workflow, self).__init__(parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = session
        self._schemas = self.session.query('ProjectSchema').all()
        for index, schema in enumerate(self._schemas):
            self.logger.debug('Adding schema : %s, with index %s' % (schema['name'], index))
            self.addItem(schema['name'])

    def currentItem(self):
        '''Return the currently selected item.'''
        currentIndex = self.currentIndex()
        result = self._schemas[currentIndex]
        self.logger.debug('Current Item: %s' % result)
        return result
