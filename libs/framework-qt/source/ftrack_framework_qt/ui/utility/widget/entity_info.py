# :coding: utf-8
# :copyright: Copyright (c) 2019-2022 ftrack
import os

from Qt import QtWidgets, QtCore


class EntityInfo(QtWidgets.QWidget):
    '''Widget presenting basic information about an entity(context)'''

    pathReady = QtCore.Signal(object)  # List if context parents are provided

    @property
    def entity(self):
        '''Return the current entity'''
        return self._entity

    @entity.setter
    def entity(self, value):
        '''Set the entity for this widget to *value*'''
        if not value:
            return
        self._entity = value
        parent = value['parent']
        parents = [value]
        while parent is not None:
            parents.append(parent)
            parent = parent['parent']
        parents.reverse()
        self.pathReady.emit(parents)

    def __init__(self, additional_widget=None, parent=None):
        '''
        Instantiate the entity info widget

        :param additional_widget: The optional insertion widget
        :param parent: The parent dialog or frame
        '''
        super(EntityInfo, self).__init__(parent=parent)

        self._entity = None

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
        self.layout().addWidget(self._path_field)

        self.layout().addStretch()

    def post_build(self):
        self.pathReady.connect(self._on_path_ready)

    def _on_path_ready(self, parents):
        '''Set current path to *names*.'''
        self.set_name_field(parents[-1]['name'])
        self.set_path_field(os.sep.join([p['name'] for p in parents[:-1]]))

    def set_name_field(self, name):
        self._name_field.setText(name)

    def set_path_field(self, path):
        self._path_field.setText(path)
