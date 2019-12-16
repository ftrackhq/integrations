# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import time
import logging

import ftrack_api

from ftrack_connect_pipeline import constants


class HostConnection(object):

    @property
    def data(self):
        return self._raw_host_data['definitions']

    @property
    def id(self):
        return self._raw_host_data['host_id']

    def __repr__(self):
        return '<HostConnection: {}>'.format(self.id)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __init__(self, event_manager, host_data):
        self.event_manager = event_manager
        self._raw_host_data = host_data

    def run(self, data):
        '''Send *data* to the host through the given *topic*.'''
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_HOST_RUN,
            data={
                'pipeline': {
                    'host_id': self.id,
                    'data': data,
                }
            }
        )
        self.event_manager.publish(
            event,
            mode=constants.REMOTE_EVENT_MODE
        )


class Client(object):
    '''
    Base client widget class.
    '''

    @property
    def connected(self):
        return self._connected

    @property
    def hosts(self):
        '''Return the current ui type.'''
        return self._host_list

    def __init__(self, event_manager, ui):
        '''Initialise widget with *ui* , *host* and *hostid*.'''
        #super(BasePipelineClient, self).__init__()
        self._packages = {}
        self._current = {}
        self._ui = ui
        self._host_list = []
        self._connected = False

        self.__callback = None
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.event_manager = event_manager
        self.session = event_manager.session

    def discover_hosts(self, time_out=3):
        # discovery host loop and timeout.
        start_time = time.time()
        self.logger.info('time out set to {}:'.format(time_out))
        if not time_out:
            self.logger.warning(
                'Running client with no time out.'
                'Will not stop until discover a host.'
                'Terminate with: Ctrl-C'
            )

        while not self.hosts:
            delta_time = time.time() - start_time

            if time_out and delta_time >= time_out:
                self.logger.warning('Could not discover any host.')
                break

            self._discover_hosts()

        if self.__callback:
            self.logger.info(
                'calling {} with {}'.format(self.__callback, self.hosts)
            )
            self.__callback(self.hosts)

    def _host_discovered(self, event):
        '''callback to to add new hosts *event*.'''
        if not event['data']:
            return

        host_connection = HostConnection(self.event_manager, event['data'])
        if host_connection not in self.hosts:
            self._host_list.append(host_connection)



    def _discover_hosts(self):
        '''Event to discover new available hosts.'''
        self._host_list = []
        discover_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_HOST
        )

        self.event_manager.publish(
            discover_event,
            callback=self._host_discovered
        )

    def on_ready(self, callback, time_out=3):
        self.__callback = callback
        self.discover_hosts(time_out=time_out)