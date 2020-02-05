# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import time
import logging
import copy
import ftrack_api

from ftrack_connect_pipeline import constants


class HostConnection(object):

    @property
    def session(self):
        '''Return session'''
        return self._event_manager.session

    @property
    def state(self):
        '''
        Return current state of the host connection.
        This will always return False, unless the publish has been successful.
        '''
        return all(
            [
                constants.status_bool_mapping.get(
                    log['status'], constants.UNKNOWN_STATUS
                )
                for log in self.logs or [
                    {'status': constants.UNKNOWN_STATUS}
                ]
            ]
        )

    @property
    def logs(self):
        return self.__logs

    @property
    def definitions(self):
        return self._raw_host_data['definition']

    @property
    def id(self):
        return self._raw_host_data['host_id']

    @property
    def host_definitions(self):
        return self._raw_host_data['host_id'].split("-")[0].split(".")

    def __del__(self):
        self.logger.debug('Closing {}'.format(self))

    def __repr__(self):
        return '<HostConnection: {}>'.format(self.id)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __init__(self, event_manager, host_data):
        '''Initialise with *event_manager* , and *host_data*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.

        *host_data* Diccionary containing the host information.
        '''
        self.logger = logging.getLogger(
            '{0}.{1}'.format(__name__, self.__class__.__name__)
        )

        copy_data = copy.deepcopy(host_data)

        self.__logs = []
        self._event_manager = event_manager
        self._raw_host_data = copy_data

        self.on_client_notification()

    def run(self, data):
        '''Send *data* to the host through the PIPELINE_HOST_RUN topic.'''
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_HOST_RUN,
            data={
                'pipeline': {
                    'host_id': self.id,
                    'data': data,
                }
            }
        )
        self._event_manager.publish(
            event
        )

    def _notify_client(self, event):
        '''callback to notify the client with the *event* data'''
        result = event['data']['pipeline']['result']
        status = event['data']['pipeline']['status']
        plugin_name = event['data']['pipeline']['plugin_name']
        widget_ref = event['data']['pipeline']['widget_ref']
        message = event['data']['pipeline']['message']

        if constants.status_bool_mapping[status]:
            self.__logs.append(event['data']['pipeline'])

            self.logger.debug(
                'plugin_name: {} \n status: {} \n result: {} \n '
                'message: {}'.format(
                    plugin_name, status, result, message
                )
            )

        if (
                status == constants.ERROR_STATUS or
                status == constants.EXCEPTION_STATUS
        ):
            raise Exception(
                'An error occurred during the execution of the '
                'plugin name {} \n message: {} \n data: {}'.format(
                    plugin_name, message, result
                )
            )

    def on_client_notification(self):
        '''Subscribe to PIPELINE_CLIENT_NOTIFICATION topic to receive client
        notifications from the host'''
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.hostid={}'.format(
                constants.PIPELINE_CLIENT_NOTIFICATION,
                self._raw_host_data['host_id']),
            self._notify_client
        )


class Client(object):
    '''
    Base client class.
    '''

    ui = [constants.UI]

    def __repr__(self):
        return '<Client:{0}>'.format(self.ui)

    def __del__(self):
        self.logger.debug('Closing {}'.format(self))

    @property
    def session(self):
        '''Return session'''
        return self._event_manager.session

    @property
    def connected(self):
        '''Return bool of client connected to a host'''
        return self._connected

    @property
    def hosts(self):
        '''Return the current list of hosts'''
        return self._host_list

    def __init__(self, event_manager):
        '''Initialise with *event_manager* , and optional *ui* List

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.

        *ui* List of valid ui compatibilities.
        '''
        self._packages = {}
        self._current = {}


        self._host_list = []
        self._connected = False

        self.__callback = None
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self._event_manager = event_manager
        self.logger.info('Initialising {}'.format(self))

    def discover_hosts(self, time_out=3):
        '''Returns a list of discovered hosts during the optional *time_out*'''
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

        if self.__callback and self.hosts:
            self.__callback(self.hosts)

        return self.hosts

    def _host_discovered(self, event):
        '''callback, adds new hosts connection from the given *event*'''
        if not event['data']:
            return
        host_connection = HostConnection(self._event_manager, event['data'])
        if host_connection not in self.hosts:
            self._host_list.append(host_connection)

        self._connected = True

    def _discover_hosts(self):
        '''Event to discover new available hosts.'''
        self._host_list = []
        discover_event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_HOST
        )

        self._event_manager.publish(
            discover_event,
            callback=self._host_discovered
        )

    def on_ready(self, callback, time_out=3):
        '''calls the given *callback* when host is been discovered with the
        optional *time_out*

        *callback* Function to call when a host has been discovered

        *time_out* Optional time out time to look for a host

        '''
        self.__callback = callback
        self.discover_hosts(time_out=time_out)
