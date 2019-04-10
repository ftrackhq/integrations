# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import ftrack_api
import logging

from qtpy import QtWidgets, QtCore

from ftrack_connect_pipeline import event
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline import constants
from ftrack_connect.ui.widget import header
from ftrack_connect.ui import theme


class BaseQtPipelineWidget(QtWidgets.QWidget):
    '''
    Base client widget class.
    '''

    hostid_changed = QtCore.Signal()

    @property
    def widgets(self):
        '''Return registered plugin's widgets.'''
        return self._widgets_ref

    @property
    def hostid(self):
        '''Return the current hostid.'''
        return self._hostid

    @property
    def host(self):
        '''Return the current host type.'''
        return self._host

    @property
    def ui(self):
        '''Return the current ui type.'''
        return self._ui

    def __init__(self, ui, host, hostid=None, parent=None):
        '''Initialise widget with *ui* , *host* and *hostid*.'''
        super(BaseQtPipelineWidget, self).__init__(parent=parent)

        self._widgets_ref = {}
        self._ui = ui
        self._host = host
        self._hostid = hostid

        self._remote_events = bool(os.environ.get(
            constants.PIPELINE_REMOTE_EVENTS_ENV, False
        ))

        self.logger = logging.getLogger(
            'ftrack_connect_pipeline.'+__name__ + '.' + self.__class__.__name__
        )

        self.session = get_shared_session()
        self.event_manager = event.EventManager(self.session)
        self.event_thread = event.NewApiEventHubThread()
        self.event_thread.start(self.session)

        self.pre_build()
        self.build()
        self.post_build()

        if not self.hostid:
            self.discover_hosts()

        # apply styles
        # theme.applyTheme(self, 'dark', 'cleanlooks')
        theme.applyFont()

    def _fetch_defintions(self, definition_type, callback):
        '''Helper to retrieve defintion for *definition_type* and *callback*.'''
        publisher_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_DEFINITION_TOPIC,
            data={
                'pipeline': {
                    'type': definition_type,
                    'hostid': self.hostid
                }
            }
        )
        self.event_manager.publish(
            publisher_event,
            callback=callback,
            remote=self._remote_events
        )

    def on_change_host(self, index):
        '''triggered when chaging host selection to *index*'''
        hostid = self.combo_hosts.itemData(index)

        self._hostid = hostid
        self.hostid_changed.emit()

        # notify host we are connected
        hook_host_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_CONNECT_CLIENT,
            data={
                'pipeline': {'hostid': hostid}
            }
        )

        self.event_manager.publish(
            hook_host_event,
            remote=self._remote_events
        )

    def _host_discovered(self, event):
        '''callback to to add new hosts *event*.'''
        hostid = str(event['data'])
        self.combo_hosts.addItem(hostid, hostid)

    def discover_hosts(self):
        '''Event to discover new available hosts.'''
        discover_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_HOST
        )

        self.event_manager.publish(
            discover_event,
            callback=self._host_discovered,
            remote=self._remote_events
        )

    def resetLayout(self, layout):
        '''Reset layout and delete widgets.'''
        self._widgets_ref = {}
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.resetLayout(item.layout())

    def pre_build(self):
        '''Prepare general layout.'''
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.combo_hosts = QtWidgets.QComboBox()
        self.layout().addWidget(self.combo_hosts)
        self.combo_hosts.addItem('- Select host -')

        if self.hostid:
            self.combo_hosts.setVisible(False)

        self.header = header.Header(self.session.api_user)
        self.layout().addWidget(self.header)
        self.combo = QtWidgets.QComboBox()
        self.layout().addWidget(self.combo)
        self.task_layout = QtWidgets.QVBoxLayout()
        self.layout().addLayout(self.task_layout)
        self.run_button = QtWidgets.QPushButton('Run')
        self.layout().addWidget(self.run_button)

    def build(self):
        '''Build widgets and parent them.'''
        raise NotImplementedError()

    def post_build(self):
        '''Post Build ui method for events connections.'''
        self.combo_hosts.currentIndexChanged.connect(self.on_change_host)
        self.run_button.clicked.connect(self._on_run)
        self.hostid_changed.connect(self._listen_widget_updates)

    def _fetch_widget(self, plugin, plugin_type, plugin_name):
        '''Retrieve widget for the given *plugin*, *plugin_type* and *plugin_name*.'''

        plugin_options = plugin.get('options', {})
        name = plugin.get('name', 'no name provided')
        description = plugin.get('description', 'No description provided')

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'plugin_name': plugin_name,
                    'plugin_type': plugin_type,
                    'type': 'widget',
                    'ui': self.ui,
                    'host': self.host,
                },
                'settings':
                    {
                        'options': plugin_options,
                        'name': name,
                        'description': description,
                    }
            }
        )

        default_widget = self.session.event_hub.publish(
            event,
            synchronous=True
        )

        return default_widget

    def _update_widget(self, event):
        self.logger.info('_update_widget:{}'.format(event))

        data = event['data']['pipeline']['data']
        widget_ref = event['data']['pipeline']['widget_ref']
        widget = self.widgets.get(widget_ref)
        if not widget:
            self.logger.warning('Widget ref :{} not found ! '.format(widget_ref))
            return

        self.logger.info('updating widget: {} with {}'.format(widget, data))
        widget.setDisabled(True)

    def _listen_widget_updates(self):
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.hostid={}'.format(constants.PIPELINE_UPDATE_UI, self.hostid),
            self._update_widget
        )

    def _fetch_default_widget(self, plugin, plugin_type):
        '''Retrieve the default widget based on *plugin* and *plugin_type*'''
        plugin_name = 'default.widget'
        return self._fetch_widget(plugin, plugin_type, plugin_name)

    # widget handling
    def fetch_widget(self, plugin, plugin_type):
        '''Retrieve widget for the given *plugin*, *plugin_type*.'''

        plugin_name = plugin.get('widget')
        result_widget = self._fetch_widget(plugin, plugin_type, plugin_name)
        if not result_widget:
            result_widget = self._fetch_default_widget(plugin, plugin_type)

        self.logger.info(result_widget)

        return result_widget[0]

    def send_to_host(self, data, topic):
        '''Send *data* to the host through the given *topic*.'''
        event = ftrack_api.event.base.Event(
            topic=topic,
            data={
                'pipeline':{
                    'hostid':self.hostid,
                    'data': data,
                }
            }
        )
        self.event_manager.publish(
            event,
            remote=self._remote_events
        )

    def _on_run(self):
        raise NotImplementedError()