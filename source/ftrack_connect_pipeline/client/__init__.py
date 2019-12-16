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


class HostConnection(object):

    @property
    def id(self):
        return self._raw_host_data['hostid']

    def __repr__(self):
        return '<HostConnection: {}>'.format(self.id)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __init__(self, session, host_data):
        self.session = session
        self._raw_host_data = host_data

    def run(self, data):
        '''Send *data* to the host through the given *topic*.'''
        topic = constants.PIPELINE_RUN_HOST_PUBLISHER
        event = ftrack_api.event.base.Event(
            topic=topic,
            data={
                'pipeline': {
                    'hostid': self.id,
                    'data': data,
                }
            }
        )
        self.event_manager.publish(
            event,
            remote=True
        )





class BasePipelineClient(object):
    '''
    Base client widget class.
    '''

    @property
    def hosts(self):
        '''Return the current ui type.'''
        return self._host_list

    def __init__(self, session, ui):
        '''Initialise widget with *ui* , *host* and *hostid*.'''
        #super(BasePipelineClient, self).__init__()
        self._packages = {}
        self._current = {}
        self._ui = ui
        self._host_list = []

        self._remote_events = utils.remote_event_mode()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.session = session
        self.event_manager = event.EventManager(self.session)
        self.event_thread = event.EventHubThread()
        self.event_thread.start(self.session)

        while not self.hosts:
            self.discover_hosts()

    def _host_discovered(self, event):
        '''callback to to add new hosts *event*.'''
        if not event['data']:
            return

        host_connection = HostConnection(self.session, event['data'])
        if host_connection not in self.hosts:
            self._host_list.append(host_connection)

    def discover_hosts(self):
        '''Event to discover new available hosts.'''
        #clear self.host_ids_l before discover hosts
        self._host_list = []
        discover_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_HOST
        )

        self.event_manager.publish(
            discover_event,
            callback=self._host_discovered,
            remote=self._remote_events
        )