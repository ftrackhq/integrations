
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

    def filter_by_host(self, json_data, host):
        json_copy = copy.deepcopy(json_data)
        for definition_name, values in json_data.items():
            for definition in values:
                if definition.get('host') and definition.get('host') != host:
                    idx = json_copy[definition_name].index(definition)
                    json_copy[definition_name].pop(idx)
        return json_copy

    def parse_dictonary(self, data, value_filter, new_list):
        if isinstance(data, dict):
            if data.get('type') == value_filter:
                new_list.append(data)
            else:
                for key, value in data.items():
                    self.parse_dictonary(value, value_filter, new_list)
        if isinstance(data, list):
            for item in data:
                self.parse_dictonary(item, value_filter, new_list)

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
