# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import copy
from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline import client
from ftrack_connect_pipeline_qt.ui.widget import header, host_selector
from ftrack_connect_pipeline_qt.client.widgets.json import factory
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline import constants as core_constants


class QtHostConnection(client.HostConnection):

    def __init__(self, event_manager, host_data):
        super(QtHostConnection, self).__init__(event_manager, host_data)


class QtClient(client.Client, QtWidgets.QWidget):
    '''
    Base client widget class.
    '''

    host_connection = None
    schema = None
    definition = None
    ui = [constants.UI]

    def __init__(self, event_manager, ui=None, parent=None):
        '''Initialise widget with *ui* , *host* and *hostid*.'''
        QtWidgets.QWidget.__init__(self, parent=parent)
        client.Client.__init__(self, event_manager, ui=ui)
        self.widget_factory = factory.WidgetFactory(
            event_manager,
            self.ui
        )
        self.pre_build()
        self.post_build()

    def _host_discovered(self, event):
        '''callback to to add new hosts *event*.'''
        current_hosts = copy.deepcopy(self.hosts)
        super(QtClient, self)._host_discovered(event)
        new_conections = []
        if current_hosts:
            new_conections = list(set(current_hosts) - set(self.hosts))
        else:
            new_conections = self.hosts
        for new_connection in new_conections:
            self.host_selector.addHost(new_connection.id, new_connection)

    def pre_build(self):
        '''Prepare general layout.'''
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.header = header.Header(self.session)
        self.layout().addWidget(self.header)

        self.host_selector = host_selector.HostSelector()
        self.layout().addWidget(self.host_selector)

        self.scroll = QtWidgets.QScrollArea()

        self.layout().addWidget(self.scroll)

        self.run_button = QtWidgets.QPushButton('Run')
        self.layout().addWidget(self.run_button)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.host_selector.definition_changed.connect(self._definition_changed)
        self.run_button.clicked.connect(self._on_run)

        self.widget_factory.widget_status_updated.connect(
            self._on_widget_status_updated
        )

    def _update_widget(self, event):
        # TODO: This can be happening at the factory
        '''*event* callback to update widget with the current status/value'''
        data = event['data']['pipeline']['data']
        widget_ref = event['data']['pipeline']['widget_ref']
        status = event['data']['pipeline']['status']
        message = event['data']['pipeline']['message']

        widget = self.widget_factory.widgets.get(widget_ref)
        if not widget:
            self.logger.warning('Widget ref :{} not found ! '.format(widget_ref))
            return

        self.logger.debug('updating widget: {} with {}'.format(widget, data))

        widget.set_status(status, message)

    def _listen_widget_updates(self):
        # TODO: This can be happening at the factory

        # TODO: We use to use the topic constants.PIPELINE_UPDATE_UI but the
        #  runner.py rises the notification with the new topic name So we have
        #  to decide if publish two diferent topics or use the new one.
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.hostid={}'.format(
                core_constants.PIPELINE_CLIENT_NOTIFICATION,
                self.host_connection.id
            ),
            self._update_widget
        )

    def _definition_changed(self, host_connection, schema, definition):
        self.host_connection = host_connection
        self.schema = schema
        self.definition = definition
        self.widget_factory.set_host_definitions(
            self.host_connection.host_definitions
        )

        if self.__callback:
            output_dict = {"host_connection": self.host_connection,
                           "schema": self.schema,
                           "definition": self.definition}
            self.__callback(output_dict)

        self._current_def = self.widget_factory.create_widget(
            "testSchema",
            schema,
            self.definition
        )
        self.scroll.setWidget(self._current_def)
        self._listen_widget_updates()# TODO: This can be happening at the factory

    def _on_widget_status_updated(self, data):
        status, message = data
        self.header.setMessage(message, status)

    def on_ready(self, callback, time_out=3):
        self.discover_hosts(time_out=time_out)
        self.__callback = callback

    def _on_run(self):
        serialized_data= self._current_def.to_json_object()
        print "serialized_data ---> {}".format(serialized_data)
        self.host_connection.run(serialized_data)