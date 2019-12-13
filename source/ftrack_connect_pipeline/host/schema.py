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

    def __init__(self, session):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(BaseSchemaManager, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.__registry = {}
        self.session = session
        self.event_manager = EventManager(self.session)
        self.register()

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

        for schema_result in result:
            schema_type = schema_result['title']
            if schema_type in self.__registry:
                self.logger.warning('{} already registered!'.format(schema_type))
                return
            self.logger.info('Registering {}'.format(schema_type))
            self.__registry[schema_type] = schema_result

    def register(self):
        '''register package'''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'type': "schema"#str(schema_type)
                }
            }
        )

        self.event_manager.publish(
            event,
            self.on_register_schema,
            remote=True
        )

class SchemaManager(object):
    '''class wrapper to contain all the definition managers.'''

    def __init__(self, session):
        super(SchemaManager, self).__init__()

        self.session = session
        self.schemas = BaseSchemaManager(session)

        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.type={}'.format(
                constants.PIPELINE_REGISTER_SCHEMA_TOPIC, "schema"),
            self.schemas.result
        )

    def validate_package(self, schema):
        _validate(schema, self.schemas.result()["Package"])

    def validate_publisher(self, schema):
        _validate(schema, self.schemas.result()["Publisher"])

    def validate_loader(self, schema):
        _validate(schema, self.schemas.result()["Loader"])
