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
            print 'discovering...'
            self.discover_hosts()

        print 'HOSTLIST:', self.hosts

    def _host_discovered(self, event):
        '''callback to to add new hosts *event*.'''
        self.logger.info('_host_discovered : {}'.format(event))
        if not event['data']:
            return
        self._host_list.append(event['data'])

    def discover_hosts(self):
        '''Event to discover new available hosts.'''
        #clear self.host_ids_l before discover hosts
        self._host_list=[]
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
