# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


import logging
import ftrack_api
import json

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.event import EventManager
from functools import partial

logger = logging.getLogger(__name__)


class BaseDefinitionManager(object):

    def result(self, *args, **kwargs):
        '''Return the result definitions.'''
        return self.__registry

    def __init__(self, session, host):
        '''Initialise the class with ftrack *session* and *context_type*'''
        super(BaseDefinitionManager, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.__registry = {}
        self.host = host
        self.session = session
        self.event_manager = EventManager(self.session)
        self.register()

    def on_register_definition(self, event):
        '''Register definition coming from *event* and store them.'''
        raw_result = event['data']
        print "on register definition ---> {}".format(raw_result)
        result = raw_result

        if not result:
            return

        parsedResult = self._parese_json(result, self.host)

        #validate here

        print "This is the final json {}".format(parsedResult)
        for obj in parsedResult['publisher']:
            print obj

        self.__registry = parsedResult

    def _parese_json(self, jsonResult, host):
        parsedJson = {}
        for definition in jsonResult:
            if parsedJson.has_key(definition['type']):
                if definition.has_key('host'):
                    if definition.get('host') == host:
                        parsedJson[definition['type']][definition['host']] = [definition]
                    '''if parsedJson[definition['type']].has_key(definition['host']):
                        parsedJson[definition['type']][definition['host']].append(definition)
                    else:
                        parsedJson[definition['type']][definition['host']] = [definition]'''
                else:
                    parsedJson[definition['type']].append(definition)
            else:
                if definition.has_key('host'):
                    if definition.get('host') == host:
                        parsedJson[definition['type']] = [definition]
                    #parsedJson[definition['type']]={definition['host']:[definition]}
                else:
                    parsedJson[definition['type']] = [definition]
        return parsedJson

    def register(self):
        '''register package'''

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_REGISTER_TOPIC,
            data={
                'pipeline': {
                    'type': "definition"
                }
            }
        )

        self.event_manager.publish(
            event,
            self.on_register_definition,
            remote=True
        )


class DefintionManager(object):
    '''class wrapper to contain all the definition managers.'''


    def __init__(self, session, host):
        super(DefintionManager, self).__init__()

        self.session = session

        self.definitions = BaseDefinitionManager(session, host)

        self.json_definitions = self.definitions.result()

        '''#Why do we use this one?
        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.type={}'.format(
                constants.PIPELINE_REGISTER_SCHEMA_TOPIC, "definition"),
            self.schemas.result
        )'''