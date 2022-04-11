# :coding: utf-8
# :copyright: Copyright (c) 2019-2022 ftrack
import os

from Qt import QtWidgets, QtCore


class EntityInfo(QtWidgets.QWidget):
    '''Entity path widget.'''

    pathReady = QtCore.Signal(object)

    def __init__(self, additional_widget=None, parent=None):
        '''Instantiate the entity path widget.'''
        super(EntityInfo, self).__init__(parent=parent)

        self._additional_widget = additional_widget

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(2, 6, 2, 2)
        self.layout().setSpacing(2)

    def build(self):
        name_widget = QtWidgets.QWidget()
        name_widget.setLayout(QtWidgets.QHBoxLayout())
        name_widget.layout().setContentsMargins(0, 0, 0, 0)
        name_widget.layout().setSpacing(0)

        self._name_field = QtWidgets.QLabel()
        self._name_field.setObjectName('h3')
        name_widget.layout().addWidget(self._name_field)
        if self._additional_widget:
            name_widget.layout().addWidget(self._additional_widget)
        name_widget.layout().addStretch()
        self.layout().addWidget(name_widget)

        self._path_field = QtWidgets.QLabel()
        self._path_field.setObjectName('gray')
        # self._path_field.setProperty('color', 'gray')
        self.layout().addWidget(self._path_field)

        self.layout().addStretch()

    def post_build(self):
        self.pathReady.connect(self.on_path_ready)

    def set_entity(self, entity):
        '''Set the *entity* for this widget.'''
        if not entity:
            return
        parent = entity['parent']
        parents = [entity]
        while parent is not None:
            parents.append(parent)
            parent = parent['parent']
        parents.reverse()
        self.pathReady.emit(parents)

    def on_path_ready(self, parents):
        '''Set current path to *names*.'''
        # self.type_field.setText(parents[-1].get('type', {}).get('name', 'Project'))
        self._name_field.setText('{} '.format(parents[-1]['name']))
        self._path_field.setText(
            os.sep.join([p['name'] for p in parents[:-1]])
        )


class VersionInfo(QtWidgets.QWidget):
    def __init__(self, session=None, parent=None):
        '''Instantiate the entity path widget.'''
        super(VersionInfo, self).__init__(parent=parent)
        self.session = session
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

    def set_entity(self, version_id):
        version = self.session.get('AssetVersion', version_id)
        self.date_field.setText(
            'Date : {}'.format(str(version['date'].humanize()))
        )
        self.user_field.setText(
            'User : {}'.format(
                str(version['user'].get('username', 'No User set'))
            )
        )
        self.description_field.setText(
            'Comment : {}'.format(
                str(version.get('comment') or 'No Comment set')
            )
        )
