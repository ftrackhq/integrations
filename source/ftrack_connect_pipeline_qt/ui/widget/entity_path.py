# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from Qt import QtWidgets, QtCore


class EntityPath(QtWidgets.QLineEdit):
    '''Entity path widget.'''
    path_ready = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        '''Instantiate the entity path widget.'''
        super(EntityPath, self).__init__(*args, **kwargs)
        self.setReadOnly(True)

        self.post_build()

    def post_build(self):
        self.path_ready.connect(self.on_path_ready)

    def setEntity(self, entity):
        '''Set the *entity* for this widget.'''
        if not entity:
            return

        parent = entity['parent']
        parents = [entity['name']]

        while parent is not None:
            parents.append(parent['name'])
            parent = parent['parent']

        parents.reverse()

        full_path = ' / '.join(parents)
        self.path_ready.emit(full_path)

    def on_path_ready(self, full_path):
        '''Set current path to *names*.'''
        self.setText(full_path)
