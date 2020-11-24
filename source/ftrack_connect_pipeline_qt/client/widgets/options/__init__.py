# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from functools import partial

from Qt import QtGui, QtCore, QtWidgets

from ftrack_connect_pipeline_qt import constants


class BaseOptionsWidget(QtWidgets.QWidget):
    '''
    Base class of a widget representation for options widgets
    '''
    status_updated = QtCore.Signal(object)
    context_changed = QtCore.Signal(object, object)
    status_icons = constants.icons.status_icons
    run_plugin_clicked = QtCore.Signal(object, object)
    run_result_updated = QtCore.Signal(object)
    asset_version_changed = QtCore.Signal(object)

    # enable_run_plugin True will enable the run button to run the plugin run
    # function individually.
    enable_run_plugin = False
    # auto_fetch_on_init True will run the funtion fetch_on_init('fetch')
    # on plugin initialization
    auto_fetch_on_init = False

    def __str__(self):
        return '{} {}'.format(self.__class__.__name__, self.name)

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, value):
        '''Sets the engine_type with the given *value*'''
        self._context = value

    @property
    def asset_type(self):
        '''Returns asset_type'''
        return self._asset_type

    @asset_type.setter
    def asset_type(self, value):
        '''Sets asset type from the given *value*'''
        self._asset_type = self.session.query(
            'AssetType where short is "{}"'.format(value)
        ).first()

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

    def _set_internal_run_result(self, data):
        '''Calls the function on_{method}_callback with values returned
        from *data*, raises not implemented error if the composed name of the
        method from *data* doesn't exists'''
        method = "on_{}_callback".format(data.keys()[0])
        result = data.get(data.keys()[0])
        if hasattr(self, method):
            callback_fn = getattr(self, method)
            callback_fn(result)
        else:
            self.debug("Not implemented callback method: {}".format(method))
            raise NotImplementedError

    def set_status(self, status, message):
        '''emit the status_updated signal with the *status* and *message*'''
        self.status_updated.emit((status, message))

    def set_run_result(self, result):
        '''emit the run_result_updated signal with the *result*'''
        self.run_result_updated.emit(result)

    def fetch_on_init(self, method='fetch'):
        '''Executes the fetch method of the plugin on the initialization time'''
        self.on_run_plugin(method)

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

        self.asset_type = self.context.get(
            'asset_type', options.get('asset_type')
        )

        self.context = session.get('Context', context_id)

        # Build widget
        self.pre_build()
        self.build()
        self.post_build()
        self.run_build()

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
        self.run_result_updated.connect(self._set_internal_run_result)

    def run_build(self):
        '''Creates a run button to run the plugin individually, enable/disbale
        it with the class variable self.enable_run_plugin'''
        self.run_plugin_button = QtWidgets.QPushButton('run')
        self.run_plugin_button.clicked.connect(
            partial(self.on_run_plugin, 'run')
        )
        self.layout().addWidget(self.run_plugin_button)
        self.run_plugin_button.setVisible(self.enable_run_plugin)

    def on_run_plugin(self, method='run'):
        '''emit signal with the *method* that has to execute on the plugin'''
        self.run_plugin_clicked.emit(method, self.to_json_object())

    def on_run_callback(self, result):
        '''Callback function for plugin execution'''
        self.logger.debug("on_run_callback, result: {}".format(result))

    def to_json_object(self):
        '''Return a formated json with the data from the current widget'''
        out = {}
        out['name'] = self.name
        out['options']={}
        for key, value in self.options.items():
            out['options'][key] = value
        return out
