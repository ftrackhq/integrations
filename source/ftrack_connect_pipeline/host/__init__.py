# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import uuid
import ftrack_api
import logging

from ftrack_connect_pipeline.host.definition import DefintionManager
from ftrack_connect_pipeline.host.runner import Runner
from ftrack_connect_pipeline import constants, utils

from functools import partial


logger = logging.getLogger(__name__)


def provide_host_information(hostid, definitions, event):
    '''return the current hostid'''
    logger.debug('providing host_id: {}'.format(hostid))
    context_id = utils.get_current_context()
    host_dict = {
        'host_id': hostid,
        'context_id': context_id,
        'definitions': definitions
    }
    return host_dict



class Host(object):

    def __init__(self, event_manager, host):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(Host, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        hostid = '{}-{}'.format(host, uuid.uuid4().hex)
        self.logger.info(
            'initializing Host {}'.format(hostid)
        )
        self.hostid = hostid
        self.__registry = {}
        self.host = host
        self.session = event_manager.session
        self.event_manager = event_manager
        self.register()

    def run(self, event):
        self.logger.info('HOST RUN {}'.format(event['data']))
        # Runner(self.event_manager....)

    def on_register_definition(self, event):
        '''Register definition coming from *event* and store them.'''
        raw_result = event['data']

        if not raw_result:
            return

        validated_result = self.validate_result(raw_result)

        # validate here

        self.__registry = validated_result

        handle_event = partial(
            provide_host_information,
            self.hostid,
            validated_result
        )

        self.event_manager.subscribe(
            constants.PIPELINE_DISCOVER_HOST,
            handle_event
        )

        self.event_manager.subscribe(
            '{} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_HOST_RUN, self.hostid
            ),
            self.run
        )
        self.logger.info('host {} ready.'.format(self.hostid))

    def validate_result(self, data):
        return data

    def register(self):
        '''register package'''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'type': "definition",
                    'host': self.host
                }
            }
        )

        self.event_manager.publish(
            event,
            self.on_register_definition,
            mode=constants.REMOTE_EVENT_MODE
        )




