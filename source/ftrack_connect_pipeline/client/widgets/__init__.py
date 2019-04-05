# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
from QtExt import QtWidgets, QtCore


class BaseWidget(QtWidgets.QWidget):

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

    def set_option_result(self, value, key):
        self.logger.info('setting : {} to {}'.format(key, value))
        self._results[key] = value

    def get_option_result(self):
        return self._results

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
        self._results = {}

        self.pre_build()
        self.build()
        self.post_build()

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
