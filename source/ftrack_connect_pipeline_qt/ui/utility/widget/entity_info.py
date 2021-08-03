# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os
from Qt import QtWidgets, QtCore


class EntityInfo(QtWidgets.QWidget):
    '''Entity path widget.'''
    path_ready = QtCore.Signal(object)

    def __init__(self, *args, **kwargs):
        '''Instantiate the entity path widget.'''
        super(EntityInfo, self).__init__(*args, **kwargs)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.build()
        self.post_build()

    def build(self):
        self.type_field = QtWidgets.QLabel()
        self.name_field = QtWidgets.QLabel()
        self.path_field = QtWidgets.QLabel()

        self.layout().addWidget(self.type_field)
        self.layout().addWidget(self.name_field)
        self.layout().addWidget(self.path_field)
        self.layout().addStretch()

    def post_build(self):
        self.path_ready.connect(self.on_path_ready)

    def setEntity(self, entity):
        '''Set the *entity* for this widget.'''
        if not entity:
            return

        parent = entity['parent']
        parents = [entity]

        while parent is not None:
            parents.append(parent)
            parent = parent['parent']

        parents.reverse()

        self.path_ready.emit(parents)

    def on_path_ready(self, parents):
        '''Set current path to *names*.'''
        self.type_field.setText(parents[-1].get('type', {}).get('name', 'Project'))
        self.name_field.setText(parents[-1]['name'])
        self.path_field.setText(os.sep.join([p['name'] for p in parents[:-1]]))


class VersionInfo(QtWidgets.QWidget):

    def __init__(self, session=None, parent=None):
        '''Instantiate the entity path widget.'''
        super(VersionInfo, self).__init__(parent=parent)
        self.session=session
        self.setLayout(QtWidgets.QVBoxLayout())
        self.build()
        self.layout().addStretch()

    def build(self):
        self.date_field = QtWidgets.QLabel()
        self.user_field = QtWidgets.QLabel()
        self.description_field = QtWidgets.QLabel()

        self.layout().addWidget(self.date_field)
        self.layout().addWidget(self.user_field)
        self.layout().addWidget(self.description_field)

    def setEntity(self, version_id):
        version = self.session.get('AssetVersion', version_id)
        self.date_field.setText('Date : {}'.format(str(version['date'].humanize())))
        self.user_field.setText('User : {}'.format(str(version['user'].get('username', 'No User set'))))
        self.description_field.setText('Comment : {}'.format(str(version.get('comment') or 'No Comment set')))

