
import copy
import ftrack_api
from ftrack_connect_pipeline import constants


class BaseValidation(object):

    def __init__(self, session, schema, packages):
        self._session = session
        self._schema = schema
        self._packages = packages

    def validate(self, definition):
        if not definition:
            return False

    def _discover_plugin(self, host, plugin, plugin_type):
        '''Run *plugin*, *plugin_type*, with given *options*, *data* and *context*'''
        plugin_name = plugin['plugin']

        data = {
            'pipeline': {
                'plugin_name': plugin_name,
                'plugin_type': plugin_type,
                'type': 'plugin',
                'host': host
            }
        }
        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_DISCOVER_PLUGIN_TOPIC,
            data=data
        )

        plugin_result = self.session.event_hub.publish(
            event,
            synchronous=True
        )
        print plugin_result

        if plugin_result:
            plugin_result = plugin_result[0]

        return plugin_result


class PublisherValidation(BaseValidation):
    def __init__(self, session, schema, packages):
        super(PublisherValidation, self).__init__(session, schema, packages)

    def validate(self, definition):
        super(PublisherValidation, self).validate(definition)


class LoaderValidation(BaseValidation):
    def __init__(self, session, schema, packages):
        super(LoaderValidation, self).__init__(session, schema, packages)

    def validate(self, definition):
        super(LoaderValidation, self).validate(definition)