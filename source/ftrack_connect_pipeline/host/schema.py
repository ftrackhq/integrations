# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


import logging
import ftrack_api
import json

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.event import EventManager
from jsonschema import validate as _validate

logger = logging.getLogger(__name__)


class BaseSchemaManager(object):

    def result(self, *args, **kwargs):
        '''Return the result definitions.'''
        return self.__registry

    def __init__(self, session, schema_type):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(BaseSchemaManager, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        #self.schema_result = {}
        self.__registry = {}
        self.session = session
        self.event_manager = EventManager(self.session)
        self._schema_type = schema_type
        self.register(schema_type)

    def on_register_schema(self, event):
        '''Register definition coming from *event* and store them.'''
        raw_result = event['data']
        result = None
        try:
            result = json.loads(raw_result)
        except Exception as error:
            self.logger.warning(
                'Failed to read schema {}, error :{} for {}'.format(
                    raw_result, error, self._schema_type
                )
            )

        if not result:
            return

        title = result['title']
        if title in self.__registry:
            self.logger.warning('{} already registered!'.format(title))
            return

        self.logger.info('Registering {}'.format(result['title']))
        self.schema_result = result;
        self.__registry[title] = result

    def register(self, schema_type):
        '''register package'''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'type': str(schema_type)
                }
            }
        )

        self.event_manager.publish(
            event,
            self.on_register_schema,
            remote=True
        )


class PackageSchemaManager(BaseSchemaManager):
    '''Package schema manager class.'''

    def __init__(self, session):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(PackageSchemaManager, self).__init__(session, constants.PACKAGE_SCHEMA)


class LoaderSchemaManager(BaseSchemaManager):

    def __init__(self, session):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(LoaderSchemaManager, self).__init__(session, constants.LOADER_SCHEMA)


class PublisherSchemaManager(BaseSchemaManager):

    def __init__(self, session):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(PublisherSchemaManager, self).__init__(session, constants.PUBLISHER_SCHEMA)


class SchemaManager(object):
    '''class wrapper to contain all the definition managers.'''
    #TODO: at some point make the baseSchema to load one package schema, one loader and one publisher instead of various.
    # we can also create a class schema validators with all the validators generated in th schema manager, so we can pass the schema
    # validators to the definition instead of the schemaManager itself

    def __init__(self, session):
        super(SchemaManager, self).__init__()

        self.session = session
        self.packages = PackageSchemaManager(session)
        self.loaders = LoaderSchemaManager(session)
        self.publishers = PublisherSchemaManager(session)

        #TODO: This is not needed and should be deleted, then the result function should be set as a property
        events_types = {
            constants.PUBLISHER_SCHEMA: self.publishers.result,
            constants.LOADER_SCHEMA: self.loaders.result,
            constants.PACKAGE_SCHEMA: self.packages.result
        }

        for event_name, event_callback in events_types.items():
            self.session.event_hub.subscribe(
                'topic={} and data.pipeline.type={}'.format(
                    constants.PIPELINE_REGISTER_SCHEMA_TOPIC, event_name),
                event_callback
            )

    def validate_package(self, schema):
        _validate(schema, self.packages.result()["Package"])

    def validate_publisher(self, schema):
        _validate(schema, self.publishers.result()["Publisher"])

    def validate_loader(self, schema):
        _validate(schema, self.loaders.result()["Loader"])
