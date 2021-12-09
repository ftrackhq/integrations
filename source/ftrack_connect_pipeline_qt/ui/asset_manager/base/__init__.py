# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from functools import partial
from Qt import QtWidgets, QtCore, QtCompat, QtGui

from ftrack_connect_pipeline import constants as core_const
from ftrack_connect_pipeline_qt.ui.utility.widget.search import Search

class AssetManagerBaseWidget(QtWidgets.QWidget):
    '''Base widget of the asset manager and assembler'''

    @property
    def event_manager(self):
        '''Returns event_manager'''
        return self._event_manager

    @property
    def session(self):
        '''Returns Session'''
        return self.event_manager.session

    def init_header_content(self, layout):
        '''To be overridden by child'''
        layout.addStretch()

    @property
    def engine_type(self):
        '''Returns engine_type'''
        return self._engine_type

    @engine_type.setter
    def engine_type(self, value):
        '''Sets the engine_type with the given *value*'''
        self._engine_type = value

    def __init__(self, event_manager, parent=None):
        '''Initialise AssetManagerWidget with *event_manager*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager` instance to
        communicate to the event server.
        '''
        super(AssetManagerBaseWidget, self).__init__(parent=parent)

        self._event_manager = event_manager
        self._engine_type = None

        self.asset_entities_list = []

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        '''Prepare general layout.'''
        self.setLayout(QtWidgets.QVBoxLayout(self))

    def build(self):
        '''Build widgets and parent them.'''

        self._header = QtWidgets.QWidget()
        self._header.setLayout(QtWidgets.QHBoxLayout())
        self.init_header_content(self._header.layout())
        self.layout().addWidget(self._header)

        #self.asset_table_view = AssetManagerTableView(
        #    self.event_manager, parent=self
        #)
        #self.layout().addWidget(self.asset_table_view)

        self.layout().addStretch()

    def post_build(self):
        '''Post Build ui method for events connections.'''
        pass

    def init_search(self):
        '''Create search box'''
        self._search = Search()
        self._search.input_updated.connect(self.on_search)
        return self._search

    def on_search(self, text):
        '''Search in the current model.'''
        pass

    def set_host_connection(self, host_connection):
        '''Sets :obj:`host_connection` with the given *host_connection*.'''
        self.host_connection = host_connection
        self._listen_widget_updates()
        #self.asset_table_view.set_host_connection(self.host_connection)

    def set_context_actions(self, actions):
        '''Set the :obj:`engine_type` into the asset_table_view and calls the
        create_action function of the same class with the given *actions*'''
        #self.asset_table_view.engine_type = self.engine_type
        #self.asset_table_view.create_actions(actions)

    def _update_widget(self, event):
        '''*event* callback to update widget with the current status/value'''
        pass

    def _listen_widget_updates(self):
        '''Subscribe to the PIPELINE_CLIENT_NOTIFICATION topic to call the
        _update_widget function when the host returns and answer through the
        same topic'''

        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                core_const.PIPELINE_CLIENT_NOTIFICATION,
                self.host_connection.id
            ),
            self._update_widget
        )

