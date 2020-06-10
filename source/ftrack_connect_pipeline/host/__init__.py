# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import uuid
import ftrack_api
import logging

from ftrack_connect_pipeline.host import engine
from ftrack_connect_pipeline.host import validation
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
        'definition': definitions
    }
    return host_dict


class Host(object):

    host = [constants.HOST]

    def __repr__(self):
        return '<Host:{0}>'.format(self.hostid)

    def __del__(self):
        self.logger.debug('Closing {}'.format(self))

    @property
    def hostid(self):
        '''Return current hostid'''
        return self._hostid

    @property
    def session(self):
        '''Return session'''
        return self._event_manager.session

    def __init__(self, event_manager):
        '''Initialise Host Class with *event_manager* and *host*(optional)

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager`instance to
        communicate to the event server.

        *host* is a list of valid host definitions.(optional)'''
        super(Host, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._hostid = '{}-{}'.format('.'.join(self.host), uuid.uuid4().hex)

        self.logger.info(
            'initializing {}'.format(self)
        )
        self._event_manager = event_manager
        self.register()

    def run(self, event):
        data = event['data']['pipeline']['data']

        try:
            validation.validate_schema(self.__registry['schema'], data)
        except Exception as error:
            self.logger.error("Can't validate the data {} "
                              "error: {}".format(data, error))
            return False

        asset_type = self.get_asset_type_from_packages(
            self.__registry['package'], data['package'])
        schema_engine = data['_config']['engine']
        MyEngine = engine.getEngine(engine.BaseEngine, schema_engine)
        engine_runner = MyEngine(self._event_manager, self.host, self.hostid,
                                 asset_type)
        runnerResult = engine_runner.run(data)

        if runnerResult == False:
            self.logger.error("Couldn't publish the data {}".format(data))

        return runnerResult

    def get_asset_type_from_packages(self, packages, data_package):
        for package in packages:
            if package['name'] == data_package:
                return package['asset_type']

    def on_register_definition(self, event):
        '''Register definition coming from *event* and store them.'''
        raw_result = event['data']

        if not raw_result:
            return

        validated_result = self.validate(raw_result)

        for key, value in list(validated_result.items()):
            logger.info('Valid packages : {} : {}'.format(key, len(value)))

        self.__registry = validated_result

        handle_event = partial(
            provide_host_information,
            self.hostid,
            validated_result
        )

        self._event_manager.subscribe(
            constants.PIPELINE_DISCOVER_HOST,
            handle_event
        )

        self._event_manager.subscribe(
            '{} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_HOST_RUN, self.hostid
            ),
            self.run
        )
        self.logger.info('host {} ready.'.format(self.hostid))

    def validate(self, data):

        plugin_validator = validation.PluginDiscoverValidation(
            self.session, self.host
        )

        invalid_publishers_idxs = plugin_validator.validate_publishers_plugins(
            data['publisher'])
        if invalid_publishers_idxs:
            for idx in sorted(invalid_publishers_idxs, reverse=True):
                data['publisher'].pop(idx)

        invalid_loaders_idxs = plugin_validator.validate_loaders_plugins(
            data['loader'])
        if invalid_loaders_idxs:
            for idx in sorted(invalid_loaders_idxs, reverse=True):
                    data['loader'].pop(idx)

        return data

    def register(self):
        '''register package'''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'type': 'definition',
                    'host': self.host[-1],
                }
            }
        )

        self._event_manager.publish(
            event,
            self.on_register_definition
        )

    def reset(self):
        self._host = []
        self._hostid = None
        self.__registry = {}






