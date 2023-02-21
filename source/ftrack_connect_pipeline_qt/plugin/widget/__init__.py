# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from functools import partial

from Qt import QtGui, QtCore, QtWidgets


class BaseOptionsWidget(QtWidgets.QWidget):
    '''
    Base class of a widget representation for options widgets
    '''

    statusUpdated = QtCore.Signal(object)
    assetChanged = QtCore.Signal(object, object, object)
    runPluginClicked = QtCore.Signal(object, object)
    runResultUpdated = QtCore.Signal(object)
    assetVersionChanged = QtCore.Signal(object)
    inputChanged = QtCore.Signal(object)

    # enable_run_plugin True will enable the run button to run the plugin run
    # function individually.
    enable_run_plugin = False
    # auto_fetch_on_init True will run the function fetch_on_init('fetch')
    # on plugin initialization
    auto_fetch_on_init = False

    def __str__(self):
        return '{} {}'.format(self.__class__.__name__, self.name)

    @property
    def context_id(self):
        '''Returns the context_id'''
        return self._context_id

    @property
    def asset_type_name(self):
        '''Returns asset_type name'''
        return self._asset_type_name

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

    @options.setter
    def options(self, value):
        '''return the widget's options.'''
        self._options = value

    def set_option_result(self, value, key, cast_type=None):
        '''set the result options of value for the key.'''
        if cast_type:
            value = cast_type(value)
        self._options[key] = value

    def _set_internal_status(self, data):
        '''set the status icon with the provided *data*'''
        pass

    def _set_internal_run_result(self, data):
        '''Calls the function on_{method}_callback with values returned
        from *data*, raises not implemented error if the composed name of the
        method from *data* doesn't exist'''
        method = "on_{}_callback".format(list(data.keys())[0])
        result = data.get(list(data.keys())[0])
        if hasattr(self, method):
            callback_fn = getattr(self, method)
            callback_fn(result)
        else:
            self.logger.debug(
                "Not implemented callback method: {}".format(method)
            )
            raise NotImplementedError

    def set_status(self, status, message):
        '''emit the status_updated signal with the *status* and *message*'''
        self.statusUpdated.emit((status, message))

    def set_run_result(self, result):
        '''emit the run_result_updated signal with the *result*'''
        self.runResultUpdated.emit(result)

    def fetch_on_init(self, method='fetch'):
        '''Executes the fetch method of the plugin on the initialization time'''
        self.on_run_plugin(method)

    def toggle_status(self, show=False):
        pass

    def toggle_name(self, show=False):
        pass

    def __init__(
        self,
        parent=None,
        session=None,
        data=None,
        name=None,
        description=None,
        options=None,
        context_id=None,
        asset_type_name=None,
    ):
        '''initialise widget with *parent*, *session*, *data*, *name*,
        *description*, *options*

        *parent* : widget to parent the current widget (optional).

        *session* :  instance of :class:`ftrack_api.session.Session`

        *data* : Data dictionary for the current widget

        *name* : Name of the current widget

        *description* : Description for the current widget

        *options* : Options dictionary for the current widget

        *context_id* : Current context_id

        *asset_type_name* : Current asset_type_name

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

        self.name_label = None

        self._context_id = context_id

        self._asset_type_name = asset_type_name
        # Build widget
        self.pre_build()
        self.build()
        self.post_build()
        self.run_build()

    def pre_build(self):
        '''pre build function, mostly used setup the widget's layout.'''
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )

    def build(self):
        '''build function , mostly used to create the widgets.'''
        self.name_label = QtWidgets.QLabel(self.name.title())
        self.name_label.setObjectName('h4')
        self.name_label.setToolTip(self.description)
        self.layout().addWidget(self.name_label)

    def post_build(self):
        '''post build function , mostly used connect widgets events.'''
        self.statusUpdated.connect(self._set_internal_status)
        self.runResultUpdated.connect(self._set_internal_run_result)

    def set_asset_type_entity(self, asset_type_name):
        return asset_type_name

    def run_build(self):
        '''Creates a run button to run the plugin individually, enable/disable
        it with the class variable self.enable_run_plugin'''
        self.run_plugin_button = QtWidgets.QPushButton('RUN')
        self.run_plugin_button.setObjectName('borderless')
        self.run_plugin_button.clicked.connect(
            partial(self.on_run_plugin, 'run')
        )
        self.layout().addWidget(self.run_plugin_button)
        self.run_plugin_button.setVisible(self.enable_run_plugin)

    def on_run_plugin(self, method='run'):
        '''emit signal with the *method* that has to execute on the plugin'''
        self.runPluginClicked.emit(method, self.to_json_object())

    def on_run_callback(self, result):
        '''Callback function for plugin execution'''
        self.logger.debug("on_run_callback, result: {}".format(result))

    def on_init_nodes_callback(self, result):
        '''Callback function for plugin execution'''
        self.logger.debug("result: {}".format(result))

    def report_input(self):
        '''To be overridden.'''
        self.inputChanged.emit({'status': True, 'message': ''})

    def to_json_object(self):
        '''Return a formatted json with the data from the current widget'''
        out = {}
        out['name'] = self.name
        out['options'] = {}
        for key, value in list(self.options.items()):
            out['options'][key] = value
        return out
