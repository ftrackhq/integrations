# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
from QtExt import QtWidgets, QtCore


class BaseWidget(QtWidgets.QWidget):
    updated = QtCore.Signal()

    @property
    def session(self):
        return self._session

    @property
    def data(self):
        return self._data

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def options(self):
        return self._options

    @property
    def widgets(self):
        return self._widgets

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        super(BaseWidget, self).__init__(parent=parent)
        self.setParent(parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._widgets = {}

        self._session = session
        self._data = data
        self._name = name
        self._description = description
        self._options = options

        self.pre_build()
        self.build()
        self.post_build()

    def add_widget(self, name, widget):
        if name in self.widgets:
            raise Exception('widget with name {} already exists'.format(name))
        self._widgets[name] = widget

    def get_widget(self, name):
        if name not in self.widgets:
            raise Exception('could not find widget with name {}'.format(name))

        return self.widgets[name]

    def pre_build(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)

    def build(self):
        name_label = QtWidgets.QLabel(self.name)
        name_label.setToolTip(self.description)
        self.layout().addWidget(name_label)

    def post_build(self):
        # used to connect qt events
        pass

    def value(self):
        raise NotImplementedError()
