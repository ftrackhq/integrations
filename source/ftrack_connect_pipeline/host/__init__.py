# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import uuid
import ftrack_api
import logging
import socket

from ftrack_connect_pipeline.host import engine as host_engine
from ftrack_connect_pipeline.host import validation
from ftrack_connect_pipeline import constants, utils

from functools import partial


logger = logging.getLogger(__name__)

def provide_host_information(host_id, definitions, host_name, event):
    '''
    Returns dictionary with host id, host name, context id and definition from
    the given *host_id*, *definitions* and *host_name*.

    *host_id* : Host id

    *definitions* : Dictionary with a valid definitions

    *host_name* : Host name
    '''
    logger.debug('providing host_id: {}'.format(host_id))
    context_id = utils.get_current_context_id()
    host_dict = {
        'host_id': host_id,
        'host_name': host_name,
        'context_id': context_id,
        'definition': definitions
    }
    return host_dict


class Host(object):

    host_types = [constants.HOST_TYPE]
    '''Compatible Host types for this HOST.'''
    engines = {
        'asset_manager': host_engine.AssetManagerEngine,
        'loader': host_engine.LoaderEngine,
        'publisher': host_engine.PublisherEngine,
    }
    '''Available engines for this host.'''

    def __repr__(self):
        return '<Host:{0}>'.format(self.host_id)

    def __del__(self):
        self.logger.debug('Closing {}'.format(self))

    @property
    def host_id(self):
        '''Returns the current host id.'''
        return self._host_id

    @property
    def host_name(self):
        '''Returns the current host name'''
        if not self.host_id:
            return
        host_types = self.host_id.split("-")[0]
        host_name = '{}-{}'.format(host_types, socket.gethostname())
        return host_name

    @property
    def session(self):
        '''
        Returns instance of :class:`ftrack_api.session.Session`
        '''
        return self._event_manager.session

    def __init__(self, event_manager):
        '''
        Initialise Host with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager`
        '''
        super(Host, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self._host_id = '{}-{}'.format(
            '.'.join(self.host_types), uuid.uuid4().hex)

        self.logger.debug(
            'initializing {}'.format(self)
        )
        self._event_manager = event_manager
        self.register()

    def run(self, event):
        '''
        Runs the data with the defined engine type of the givent *event*

        Returns result of the engine run.

        *event* : Published from the client host connection at
        :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        '''
        data = event['data']['pipeline']['data']
        engine_type = event['data']['pipeline']['engine_type']
        package = data.get('package')
        asset_type_name = None

        if package:
            # we are in Load/Publish land....
            # We do this check before the load_publish engine, to validate the
            # schema and because we need the asset type to load the engine.
            asset_type_name = self.get_asset_type_from_packages(
                self.__registry['package'], package
            )
            try:
                validation.validate_schema(self.__registry['schema'], data)
            except Exception as error:
                self.logger.error(
                    "Can't validate the data {} error: {}".format(data, error)
                )

        Engine = self.engines.get(engine_type)
        engine_runner = Engine(
            self._event_manager, self.host_types, self.host_id, asset_type_name
        )

        if package:
            runner_result = engine_runner.run_definition(data)
        else:
            print("data --> {}".format(data))
            runner_result = engine_runner.run(data)
        if runner_result == False:
            self.logger.error("Couldn't publish the data {}".format(data))
        return runner_result

    def get_asset_type_from_packages(self, packages, data_package):
        '''
        Returns the asset type if the given *data_package* is in the given
        *packages*

        *packages* : Validatet packages

        *data_package* : package got from the data in the :meth:`run`
        '''
        for package in packages:
            if package['name'] == data_package:
                return package['asset_type_name']

    def on_register_definition(self, event):
        '''
        Callback of the :meth:`register`
        Validates the given *event* and subscribes to the
        :class:`ftrack_api.event.base.Event` events with the topics
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_DISCOVER_HOST`
        and :const:`~ftrack_connnect_pipeline.constants.PIPELINE_HOST_RUN`

        *event* : Should be a validated and complete definitions, schema and
        packages dictionary coming from
        :func:`ftrack_connect_pipeline_definition.resource.definitions.register.register_definitions`
        '''

        raw_result = event['data']

        if not raw_result:
            return

        validated_result = self.validate(raw_result)

        for key, value in list(validated_result.items()):
            logger.warning('Valid packages : {} : {}'.format(key, len(value)))

        self.__registry = validated_result

        handle_event = partial(
            provide_host_information,
            self.host_id,
            validated_result,
            self.host_name
        )

        self._event_manager.subscribe(
            constants.PIPELINE_DISCOVER_HOST,
            handle_event
        )

        self._event_manager.subscribe(
            '{} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_HOST_RUN, self.host_id
            ),
            self.run
        )
        self.logger.debug('host {} ready.'.format(self.host_id))

    def validate(self, data):
        '''
        Validates the given *data* against the correspondant plugin validator.
        Returns a validated data.

        *data* : Should be a validated and complete definitions, schema and
        packages dictionary coming from
        :func:`ftrack_connect_pipeline_definition.resource.definitions.register.register_definitions`
        '''
        plugin_validator = validation.PluginDiscoverValidation(
            self.session, self.host_types
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
        '''
        Publishes the :class:`ftrack_api.event.base.Event` with the topic
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_REGISTER_TOPIC`
        with the first host_type in the list :obj:`host_types` and type definition as the
        data.

        Callback of the event points to :meth:`on_register_definition`
        '''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'type': 'definition',
                    'host_type': self.host_types[-1],
                }
            }
        )

        self._event_manager.publish(
            event,
            self.on_register_definition
        )

    def reset(self):
        '''
        Empty the variables :obj:`host_type`, :obj:`host_id` and :obj:`__registry`
        '''
        self._host_type = []
        self._host_id = None
        self.__registry = {}






