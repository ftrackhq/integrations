# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
import uuid

# from ftrack_connect.ui import theme
#from Qt import QtCore, QtWidgets
import ftrack_api

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline import event
from ftrack_connect_pipeline import utils
from ftrack_connect_pipeline.session import get_shared_session


class BasePipelineClient(object):
    '''
    Base client widget class.
    '''

    @property
    def packages(self):
        return self._packages

    @property
    def schema(self):
        return self._current

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

    @property
    def availableHosts(self):
        '''Return the current ui type.'''
        return self._hosts_ids_l

    def __init__(self, ui, host, hostid=None):
        '''Initialise widget with *ui* , *host* and *hostid*.'''
        #super(BasePipelineClient, self).__init__()
        self._packages = {}
        self._current = {}
        self._ui = ui
        self._host = host
        self._hostid = hostid
        self._hosts_ids_l = [] #list of dictionaries as {"hostid":hostId, "contextid":contextid}

        self._remote_events = utils.remote_event_mode()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = get_shared_session()
        self.event_manager = event.EventManager(self.session)
        self.event_thread = event.EventHubThread()
        self.event_thread.start(self.session)

        self.fetch_package_definitions()

        if not self.hostid:
            self.discover_hosts()

    def fetch_package_definitions(self):
        self._fetch_defintions('package', self._packages_loaded)

    def _packages_loaded(self, event):
        '''event callback for when the publishers are loaded.'''
        raw_data = event['data']

        for item_name, item in raw_data.items():
            self._packages[item_name] = item

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
    def set_host_and_context(self, host_id, context_id):
        '''Change the current host and context'''
        self._context = self.session.get('Context', context_id)
        self._hostid = host_id

        # notify host we are connected
        hook_host_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_CONNECT_CLIENT,
            data={
                'pipeline': {'hostid': host_id}
            }
        )

        self.event_manager.publish(
            hook_host_event,
            remote=self._remote_events
        )

    def _host_discovered(self, event):
        '''callback to to add new hosts *event*.'''
        self.logger.debug('_host_discovered : {}'.format(event['data']))
        hostid = str(event['data']['hostid'])
        context_id = str(event['data']['context_id'])
        hostDict = {"hostid":hostid, "context_id":context_id}
        self._hosts_ids_l.add(hostDict)

    def discover_hosts(self):
        '''Event to discover new available hosts.'''
        #clear self.host_ids_l before discover hosts
        self._hosts_ids_l.clear()
        discover_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_HOST
        )

        self.event_manager.publish(
            discover_event,
            callback=self._host_discovered,
            remote=self._remote_events
        )

    def send_to_host(self, data, topic):
        '''Send *data* to the host through the given *topic*.'''
        event = ftrack_api.event.base.Event(
            topic=topic,
            data={
                'pipeline': {
                    'hostid': self.hostid,
                    'data': data,
                }
            }
        )
        self.event_manager.publish(
            event,
            remote=self._remote_events
        )
