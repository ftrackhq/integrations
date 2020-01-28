# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
from collections import OrderedDict

import uuid
import ftrack_api
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget
from ftrack_connect_pipeline_qt.client.widgets import json
from ftrack_connect_pipeline_qt.client.widgets.json.overrides import component,\
    hidden, plugin_container

from Qt import QtCore, QtWidgets


class WidgetFactory(QtWidgets.QWidget):
    ''''''

    @property
    def widgets(self):
        '''Return registered plugin's widgets.'''
        return self._widgets_ref

    widget_status_updated = QtCore.Signal(object)

    host_definitions = None
    ui=None

    schema_type_mapping = {
        'object': json.JsonObject,
        'string': json.JsonString,
        'integer': json.JsonInteger,
        'array': json.JsonArray,
        'number': json.JsonNumber,
        'boolean': json.JsonBoolean
    }
    schema_name_mapping = {
        'components': component.ComponentsArray,
        '_config': hidden.HiddenObject,
        'ui': hidden.HiddenString,
        'type': hidden.HiddenString,
        'name': hidden.HiddenString
    }

    schema_title_mapping = {
        'Plugin': plugin_container.PluginContainerObject,
        'Component': plugin_container.PluginContainerObject
    }

    def __init__(self, event_manager, ui):
        '''
        '''
        super(WidgetFactory, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = event_manager.session
        self._event_manager = event_manager
        self.ui = ui
        self._widgets_ref = {}

    def set_host_definitions(self, host_definitions):
        self.host_definitions = host_definitions

    def create_widget(self, name, schema_fragment, fragment_data=None,
                      previous_object_data=None, parent=None):
        """
            Create the appropriate widget for a given schema element.
        """
        schema_fragment_order = schema_fragment.get('order', [])

        # sort schema fragment keys by the order defined in the schema order
        # any not found entry will be added last.

        if "properties" in schema_fragment:
            schema_fragment_properties = OrderedDict(
                sorted(
                    schema_fragment['properties'].items(),
                    key=lambda pair: schema_fragment_order.index(pair[0])
                    if pair[0] in schema_fragment_order
                    else len(schema_fragment['properties'].keys()) - 1)
            )
            schema_fragment['properties'] = schema_fragment_properties

        widget_fn = self.schema_name_mapping.get(name)
        if not widget_fn:
            widget_fn = self.schema_title_mapping.get(
                schema_fragment.get('title'))
        if not widget_fn:
            widget_fn = self.schema_type_mapping.get(
                schema_fragment.get('type'), json.UnsupportedSchema)

        return widget_fn(name, schema_fragment, fragment_data,
                         previous_object_data, self, parent)

    def fetch_plugin_widget(self, plugin_data, plugin_type, extra_options=None):
        '''Retrieve widget for the given *plugin*, *plugin_type*.'''

        plugin_name = plugin_data.get('widget')
        plugin_type = plugin_type
        data = self._fetch_plugin_widget(
            plugin_data, plugin_type, plugin_name, extra_options=extra_options
        )
        if not data:
            plugin_name = 'default.widget'
            if not plugin_data.get('widget'):
                plugin_data['widget'] = plugin_name
            data = self._fetch_plugin_widget(
                plugin_data, plugin_type, plugin_name,
                extra_options=extra_options)
        data = data[0]

        message = data['message']
        result = data['result']
        status = data['status']

        if status == constants.EXCEPTION_STATUS:
            raise Exception(
                'Got response "{}"" while fetching:\n'
                'plugin: {}\n'
                'plugin_type: {}\n'
                'plugin_name: {}'.format(
                    message, plugin_data, plugin_type, plugin_name)
            )

        if result and not isinstance(result, BaseOptionsWidget):
            raise Exception(
                'Widget {} should inherit from {}'.format(
                    result,
                    BaseOptionsWidget
                )
            )

        result.status_updated.connect(self._on_widget_status_updated)
        self.register_widget_plugin(plugin_data, result)

        return result

    def _fetch_plugin_widget(self, plugin_data, plugin_type, plugin_name,
                             extra_options=None):
        '''Retrieve widget for the given *plugin*, *plugin_type* and
        *plugin_name*.'''
        extra_options = extra_options or {}
        plugin_options = plugin_data.get('options', {})
        plugin_options.update(extra_options)
        name = plugin_data.get('name', 'no name provided')
        description = plugin_data.get('description', 'No description provided')

        result = None
        for host_definition in reversed(self.host_definitions):
            for _ui in reversed(self.ui):
                event = ftrack_api.event.base.Event(
                    topic=constants.PIPELINE_RUN_PLUGIN_TOPIC,
                    data={
                        'pipeline': {
                            'plugin_name': plugin_name,
                            'plugin_type': plugin_type,
                            'type': 'widget',
                            'host': host_definition,
                            'ui': _ui
                        },
                        'settings': {
                            'options': plugin_options,
                            'name': name,
                            'description': description,
                        }
                    }
                )

                result = self.session.event_hub.publish(
                    event,
                    synchronous=True
                )

                if result:
                    break
            return result

    def _on_widget_status_updated(self, status):
        self.widget_status_updated.emit(status)

    def register_widget_plugin(self, plugin_data, widget):
        '''regiter the *widget* against the given *plugin*'''
        uid = uuid.uuid4().hex
        self._widgets_ref[uid] = widget
        plugin_data['widget_ref'] = uid

        return uid

    def get_registered_widget_plugin(self, plugin_data):
        '''return the widget registered for the given *plugin*.'''
        return self._widgets_ref[plugin_data['widget_ref']]
