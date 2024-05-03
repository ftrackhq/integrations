# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_utils.decorators import asynchronous


class EntityPath(QtWidgets.QLineEdit):
    '''Entity path widget.'''

    path_ready = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        '''Instantiate the entity path widget.'''
        super(EntityPath, self).__init__(*args, **kwargs)

        self.setReadOnly(True)
        self.path_ready.connect(self.on_path_ready)

    @asynchronous
    def setEntity(self, entity):
        '''Set the *entity* for this widget.'''
        if not entity:
            return

        names = [e['name'].strip() for e in entity.get('link', [])]

        self.path_ready.emit(names)

    def on_path_ready(self, names):
        '''Set current path to *names*.'''
        self.setText(' / '.join(names))
