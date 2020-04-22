# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging

from Qt import QtGui, QtCore, QtWidgets

from ftrack_connect_pipeline_qt import constants


class BaseOptionsWidget(QtWidgets.QWidget):
    '''
    Base class of a widget representation for options widgets
    '''
    status_updated = QtCore.Signal(object)
    status_icons = constants.icons.status_icons

    def __str__(self):
        return '{} {}'.format(self.__class__.__name__, self.name)

    @property
    def context(self):
        return self._context

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
        self._options[key] = value

    def _set_internal_status(self, data):
        '''set the status icon with the provided *data*'''
        status, message = data
        icon = self.status_icons[status]
        self._status_icon.setPixmap(icon)
        self._status_icon.setToolTip(str(message))

    def set_status(self, status, message):
        '''emit the status_updated signal with the *status* and *message*'''
        self.status_updated.emit((status, message))

    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context=None
    ):
        '''initialise widget with *parent*, *session*, *data*, *name*,
        *description*, *options*

        *parent* widget to parent the current widget (optional).

        *session* should be the :class:`ftrack_api.session.Session` instance
        to use for communication with the server.

        '''
        super(BaseOptionsWidget, self).__init__(parent=parent)
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
        self._context = context or {}

        context_id = self.context.get(
            'context_id', options.get('context_id')
        )

        asset_type = self.context.get(
            'asset_type', options.get('asset_type')
        )
        self._asset_type = session.query(
            'AssetType where short is "{}"'.format(asset_type)
        ).one()

        self._context = session.get('Context', context_id)

        # Build widget
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''pre build function, mostly used setup the widget's layout.'''
        layout = QtWidgets.QVBoxLayout()

        self._status_icon = QtWidgets.QLabel()
        icon = self.status_icons[constants.DEFAULT_STATUS]
        self._status_icon.setPixmap(icon)
        self._status_icon.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        self._status_icon.setMaximumHeight(10)

        layout.addWidget(self._status_icon)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Fixed
        )

    def build(self):
        '''build function , mostly used to create the widgets.'''
        name_label = QtWidgets.QLabel(self.name)
        name_label.setToolTip(self.description)
        self.layout().addWidget(name_label)

    def post_build(self):
        '''post build function , mostly used connect widgets events.'''
        self.status_updated.connect(self._set_internal_status)
        self.setMaximumHeight(self.sizeHint().height())

    def to_json_object(self):
        '''Return a formated json with the data from the current widget'''
        out = {}
        out['name'] = self.name
        out['options']={}
        for key, value in self.options.items():
            out['options'][key] = value
        return out
