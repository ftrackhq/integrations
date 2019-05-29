# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import uuid
import ftrack_api
import logging

from qtpy import QtWidgets, QtCore

from ftrack_connect_pipeline import event
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import utils
from ftrack_connect_pipeline.client.widgets import BaseWidget

from ftrack_connect.ui.widget import header
from ftrack_connect.ui import theme


class BaseQtPipelineWidget(QtWidgets.QWidget):
    '''
    Base client widget class.
    '''

    hostid_changed = QtCore.Signal()

    @property
    def context(self):
        return self._context

    @property
    def packages(self):
        return self._packages

    @property
    def schema(self):
        return self._current

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
        self._context = {}
        self._packages = {}
        self._current = {}
        self._widgets_ref = {}
        self._ui = ui
        self._host = host
        self._hostid = hostid

        self._remote_events = utils.remote_event_mode()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = get_shared_session()
        self.event_manager = event.EventManager(self.session)
        self.event_thread = event.NewApiEventHubThread()
        self.event_thread.start(self.session)

        self.pre_build()
        self.build()
        self.post_build()
        self.fetch_package_definitions()

        if not self.hostid:
            self.discover_hosts()
        else:
            context_id = utils.get_current_context()
            self._context = self.session.get('Context', context_id)

        # apply styles
        theme.applyTheme(self, 'dark')
        theme.applyFont()

    def fetch_package_definitions(self):
        self._fetch_defintions('package', self._packages_loaded)

    def _packages_loaded(self, event):
        '''event callback for when the publishers are loaded.'''
        raw_data = event['data']

        for item_name, item in raw_data.items():
            self._packages[item_name] = item

    def get_registered_widget_plugin(self, plugin):
        '''return the widget registered for the given *plugin*.'''
        return self._widgets_ref[plugin['widget_ref']]

    def register_widget_plugin(self, widget, plugin):
        '''regiter the *widget* against the given *plugin*'''
        uid = uuid.uuid4().hex
        self._widgets_ref[uid] = widget
        plugin['widget_ref'] = uid

        return uid

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
        results  = self.combo_hosts.itemData(index)
        if not results:
            return

        hostid, context_id = results
        self._context = self.session.get('Context', context_id)
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
        self.logger.info('_host_discovered : {}'.format(event['data']))
        hostid = str(event['data']['hostid'])
        context_id = str(event['data']['context_id'])
        self.combo_hosts.addItem(hostid, (hostid, context_id))

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
        self._listen_widget_updates()

    def _fetch_widget(self, plugin, plugin_type, plugin_name, extra_options=None):
        '''Retrieve widget for the given *plugin*, *plugin_type* and *plugin_name*.'''
        extra_options = extra_options or {}
        plugin_options = plugin.get('options', {})
        plugin_options.update(extra_options)
        name = plugin.get('name', 'no name provided')
        description = plugin.get('description', 'No description provided')

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_RUN_PLUGIN_TOPIC,
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

        result = self.session.event_hub.publish(
            event,
            synchronous=True
        )
        return result

    def _update_widget(self, event):
        '''*event* callback to update widget with the current status/value'''
        data = event['data']['pipeline']['data']
        widget_ref = event['data']['pipeline']['widget_ref']
        status = event['data']['pipeline']['status']

        widget = self.widgets.get(widget_ref)
        if not widget:
            self.logger.warning('Widget ref :{} not found ! '.format(widget_ref))
            return

        self.logger.info('updating widget: {} with {}'.format(widget, data))
        widget.set_status(status)
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
    def fetch_widget(self, plugin, plugin_type, extra_options=None):
        '''Retrieve widget for the given *plugin*, *plugin_type*.'''

        plugin_name = plugin.get('widget')
        data = self._fetch_widget(plugin, plugin_type, plugin_name, extra_options=extra_options)

        if not data:
            data = self._fetch_default_widget(plugin, plugin_type)

        data = data[0] # extract first element of the list

        status = data['status']
        result = data['result']

        if result and not isinstance(result, BaseWidget):
            raise Exception(
                'Widget {} should inherit from {}'.format(
                    result,
                    BaseWidget
                )
            )

        return result

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
        '''main run function'''
        pass