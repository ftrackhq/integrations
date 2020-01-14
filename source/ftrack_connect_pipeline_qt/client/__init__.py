# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import uuid

# from ftrack_connect.ui import theme
from Qt import QtCore, QtWidgets
import ftrack_api

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import event
from ftrack_connect_pipeline import utils
from ftrack_connect_pipeline_qt.client.widgets import BaseWidget
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline_qt.ui.widget import header
from ftrack_connect_pipeline.client import BasePipelineClient


class BaseQtPipelineWidget(BasePipelineClient, QtWidgets.QWidget):
    '''
    Base client widget class.
    '''

    hostid_changed = QtCore.Signal()

    @property
    def context(self):
        return self._context

    @property
    def widgets(self):
        '''Return registered plugin's widgets.'''
        return self._widgets_ref

    @property
    def ui(self):
        '''Return the current ui type.'''
        return self._ui

    def __init__(self, ui, host, hostid=None, parent=None):
        '''Initialise widget with *ui* , *host* and *hostid*.'''
        #super(BaseQtPipelineWidget, self).__init__(ui=ui, host=host, hostid=hostid, parent=parent)
        QtWidgets.QWidget.__init__(self, parent=parent)
        BasePipelineClient.__init__(self, ui=ui, host=host, hostid=hostid)
        self._context = {}
        self._current = {}
        self._widgets_ref = {}
        self._ui = ui
        self._host = host
        self._hostid = hostid


        '''self.session = get_shared_session()
        self.event_manager = event.EventManager(self.session)
        self.event_thread = event.EventHubThread()
        self.event_thread.start(self.session)'''

        if self.hostid:
            context_id = utils.get_current_context()
            self._context = self.session.get('Context', context_id)

        self.pre_build()
        self.build()
        self.post_build()

        # apply styles
        # theme.applyTheme(self, 'dark')
        # theme.applyFont()

    def get_registered_widget_plugin(self, plugin):
        '''return the widget registered for the given *plugin*.'''
        return self._widgets_ref[plugin['widget_ref']]

    def register_widget_plugin(self, widget, plugin):
        '''regiter the *widget* against the given *plugin*'''
        uid = uuid.uuid4().hex
        self._widgets_ref[uid] = widget
        plugin['widget_ref'] = uid

        return uid

    def on_change_host(self, index):
        '''triggered when chaging host selection to *index*'''
        results = self.combo_hosts.itemData(index)
        if not results:
            return

        hostid, context_id = results
        self.set_host_and_context(hostid, context_id)
        self.hostid_changed.emit()

    def _host_discovered(self, event):
        '''callback to to add new hosts *event*.'''
        #we run super as we want to add the discovered host to the self.hosts_ids_l
        super(BaseQtPipelineWidget, self)._host_discovered()
        hostid = str(event['data']['hostid'])
        context_id = str(event['data']['context_id'])
        self.combo_hosts.addItem(hostid, (hostid, context_id))

    def discover_hosts(self):
        '''Event to discover new available hosts.'''
        #Implemented in the base class we should be sure that is calling the _host_discovered from this class and not
        # from the base class
        super(BaseQtPipelineWidget, self).discover_hosts()

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

        self.header = header.Header(self.session)
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
                'settings': {
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
        message = event['data']['pipeline']['message']

        widget = self.widgets.get(widget_ref)
        if not widget:
            self.logger.warning('Widget ref :{} not found ! '.format(widget_ref))
            return

        self.logger.debug('updating widget: {} with {}'.format(widget, data))

        widget.set_status(status, message)

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

        data = data[0]

        message = data['message']
        result = data['result']
        status = data['status']

        if status == constants.EXCEPTION_STATUS:
            raise Exception(
                'Got response "{}"" while fetching:\n'
                'plugin: {}\n'
                'plugin_type: {}\n'
                'plugin_name: {}'.format(message, plugin, plugin_type, plugin_name)
            )

        if result and not isinstance(result, BaseWidget):
            raise Exception(
                'Widget {} should inherit from {}'.format(
                    result,
                    BaseWidget
                )
            )

        result.status_updated.connect(self.on_widget_status_updated)

        return result

    def on_widget_status_updated(self, data):
        status, message = data
        self.header.setMessage(message, status)

    def _on_run(self):
        '''main run function'''
        self.header.dismissMessage()
        pass
