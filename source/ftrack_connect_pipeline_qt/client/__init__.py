# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import copy
from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline import client
from ftrack_connect_pipeline_qt.ui.widget import header, host_selector
from ftrack_connect_pipeline_qt import widgets_schema_factory
from ftrack_connect_pipeline_qt import constants


class QtHostConnection(client.HostConnection):

    def __init__(self, event_manager, host_data):
        super(QtHostConnection, self).__init__(event_manager, host_data)


class QtClient(client.Client, QtWidgets.QWidget):
    '''
    Base client widget class.
    '''

    def __init__(self, event_manager, ui, parent=None):
        '''Initialise widget with *ui* , *host* and *hostid*.'''
        QtWidgets.QWidget.__init__(self, parent=parent)
        client.Client.__init__(self, event_manager, ui)
        self.widget_factory = widgets_schema_factory.WidgetFactory()
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
            self.combo_hosts.addItem(new_connection.id, new_connection)


    def pre_build(self):
        '''Prepare general layout.'''
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.combo_hosts = host_selector.HostComboBox()

        self.layout().addWidget(self.combo_hosts)

        self.header = header.Header(self.session)
        self.layout().addWidget(self.header)
        self.scroll = QtWidgets.QScrollArea()

        self.layout().addWidget(self.scroll)

        # self.combo = QtWidgets.QComboBox()
        # self.layout().addWidget(self.combo)
        # self.task_layout = QtWidgets.QVBoxLayout()
        # self.layout().addLayout(self.task_layout)
        # self.run_button = QtWidgets.QPushButton('Run')
        # self.layout().addWidget(self.run_button)

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.combo_hosts.hostid_changed.connect(self._host_changed)#(self._listen_widget_updates)
        # self.run_button.clicked.connect(self._on_run)
        # self._listen_widget_updates()

    def _update_widget(self, event):
        '''*event* callback to update widget with the current status/value'''
        pass
        # data = event['data']['pipeline']['data']
        # widget_ref = event['data']['pipeline']['widget_ref']
        # status = event['data']['pipeline']['status']
        # message = event['data']['pipeline']['message']
        #
        # widget = self.widgets.get(widget_ref)
        # if not widget:
        #     self.logger.warning('Widget ref :{} not found ! '.format(widget_ref))
        #     return
        #
        # self.logger.debug('updating widget: {} with {}'.format(widget, data))
        #
        # widget.set_status(status, message)

    def _listen_widget_updates(self):
        pass
        # self.session.event_hub.subscribe(
        #     'topic={} and data.pipeline.hostid={}'.format(
        #         constants.PIPELINE_UPDATE_UI, # we now have constants.PIPELINE_CLIENT_NOTIFICATION (see engine init _notify_client)
        #         self.host_conection.id
        #     ),
        #     self._update_widget
        # )

    def _host_changed(self, host_connection):
        print "host changed ---> {}".format(host_connection)
        # for now filter out everything but the publisher
        publisher_schema = [
            schema for schema in host_connection.definitions['schemas']
            if schema.get('title') == "Publisher"
        ][0]

        properties_order = publisher_schema.get('order', [])

        result = self.widget_factory.create_widget(
            "testSchema",
            publisher_schema,
            properties_order=properties_order
        )
        self.scroll.setWidget(result)