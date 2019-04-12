# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
from qtpy import QtWidgets, QtCore


class BaseWidget(QtWidgets.QWidget):

    @property
    def session(self):
        '''return current session object.'''
        return self._session

    @property
    def data(self):
        '''return the widget's data.'''
        return self._data

    @property
    def name(self):
        '''return the widget's name.'''
        return self._name

    @property
    def description(self):
        '''return the widget's description.'''
        return self._description

    @property
    def options(self):
        '''return the widget's options.'''
        return self._options

    def set_option_result(self, value, key):
        '''set the result options of value for the key.'''
        self.logger.info('setting : {} to {}'.format(key, value))
        self._results[key] = value

    def get_option_results(self):
        '''return the current option results'''
        return self._results

    def set_error(self, message=None):
        self.setStyleSheet('QWidget {color:orange}')

    def set_success(self, message=None):
        self.setStyleSheet('QWidget {color:green}')

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        '''initialise widget.'''
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

        # Build widget
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''pre build function, mostly used setup the widget's layout.'''
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)

    def build(self):
        '''build function , mostly used to create the widgets.'''
        name_label = QtWidgets.QLabel(self.name)
        name_label.setToolTip(self.description)
        self.layout().addWidget(name_label)

    def post_build(self):
        '''post build function , mostly used connect widgets events.'''
        pass
