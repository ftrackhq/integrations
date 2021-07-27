# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from collections import OrderedDict
from functools import partial

import uuid
import ftrack_api
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget
from ftrack_connect_pipeline_qt.client.widgets import schema as schema_widget
from ftrack_connect_pipeline_qt.client.widgets.schema.overrides import (
    step, hidden, plugin_container, stage
)

from Qt import QtCore, QtWidgets


class WidgetFactory(QtWidgets.QWidget):
    '''Main class to represent widgets from json schemas'''

    widget_status_updated = QtCore.Signal(object)
    widget_context_updated = QtCore.Signal(object)
    widget_asset_updated = QtCore.Signal(object, object, object)
    widget_run_plugin = QtCore.Signal(object, object)

    host_types = None
    ui_types = None

    @property
    def widgets(self):
        '''Return registered plugin's widgets.'''
        return self._widgets_ref

    @property
    def type_widgets(self):
        '''Return registered type widgets.'''
        return self._type_widgets_ref

    def __init__(self, event_manager, ui_types):
        '''Initialise WidgetFactory with *event_manager*, *ui*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager` instance to
        communicate to the event server.

        *ui_types* List of valid ux libraries.

        '''
        super(WidgetFactory, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = event_manager.session
        self._event_manager = event_manager
        self.ui_types = ui_types
        self._widgets_ref = {}
        self._type_widgets_ref = {}
        self.context_id = None
        self.asset_type_name = None
        self.host_connection = None

        self.components_names = []

        self.schema_type_mapping = {
            'object': schema_widget.JsonObject,
            'string': schema_widget.JsonString,
            'integer': schema_widget.JsonInteger,
            'array': schema_widget.JsonArray,
            'number': schema_widget.JsonNumber,
            'boolean': schema_widget.JsonBoolean
        }
        self.schema_name_mapping = {
            'components': step.StepTabArray,
            'contexts': step.StepArrayContext,
            'finalizers': step.StepTabArray,
            '_config': hidden.HiddenObject,
            'ui_type': hidden.HiddenString,
            'category': hidden.HiddenString,
            'type': hidden.HiddenString,
            'name': hidden.HiddenString,
            'enabled': hidden.HiddenBoolean,
            'package': hidden.HiddenString,
            'engine_type': hidden.HiddenString,
            'host_type': hidden.HiddenString,
            'optional': hidden.HiddenBoolean,
            'discoverable': hidden.HiddenArray,
            # 'stages': stage.AccordionStageArray
        }

        self.schema_title_mapping = {
            'Publisher': hidden.HiddenObject,
            'Loader': hidden.HiddenObject,
            'AssetManager': hidden.HiddenObject,
            'Step': hidden.HiddenObject,
            'Plugin': plugin_container.PluginContainerAccordionObject,
            'Component': plugin_container.PluginContainerObject
        }

    def set_context(self, context_id, asset_type_name):
        '''Set :obj:`context_id` and :obj:`asset_type_name` with the given
        *context_id* and *asset_type_name*'''
        self.context_id = context_id
        self.asset_type_name = asset_type_name

    def set_package(self, package):
        '''Set :obj:`package` with the given *package*'''
        self.package = package

    def set_host_connection(self, host_connection):
        '''Set :obj:`host_connection` with the given *host_connection*'''
        self.host_connection = host_connection
        self._listen_widget_updates()

    def set_definition_type(self, definition_type):
        '''Set :obj:`definition_type` with the given *definition_type*'''
        self.definition_type = definition_type

    def create_widget(
            self, name, schema_fragment, fragment_data=None,
            previous_object_data=None, parent=None):
        '''
        Create the appropriate widget for a given schema element with *name*,
        *schema_fragment*, *fragment_data*, *previous_object_data*, *parent*

        *name* : widget name

        *schema_fragment* : fragment of the schema to generate the current widget

        *fragment_data* : fragment of the data from the definition to fill
        the current widget.

        *previous_object_data* : fragment of the data from the previous schema
        fragment

        *parent* : widget to parent the current widget (optional).

        '''

        schema_fragment_order = schema_fragment.get('order', [])

        # sort schema fragment keys by the order defined in the schema order
        # any not found entry will be added last.

        if 'properties' in schema_fragment:
            schema_fragment_properties = OrderedDict(
                sorted(
                    list(schema_fragment['properties'].items()),
                    key=lambda pair: schema_fragment_order.index(pair[0])
                    if pair[0] in schema_fragment_order
                    else len(list(schema_fragment['properties'].keys())) - 1)
            )
            schema_fragment['properties'] = schema_fragment_properties


        widget_fn = self.schema_name_mapping.get(name)
        # We can remove this if we filter them on the plugin itself
        # (AccordionStageArray) But this is one more generic approach.
        # if (
        #         name == 'stages' and previous_object_data.get('type')
        #         not in ['component']
        # ):
        #     widget_fn = None

        if not widget_fn:
            widget_fn = self.schema_title_mapping.get(
                schema_fragment.get('title'))

        if not widget_fn:
            if previous_object_data:
                if previous_object_data.get('category') == 'step':
                    if (
                            name in previous_object_data.get('stage_order')
                            and schema_fragment.get('type') == 'string'
                    ):
                        widget_fn = hidden.HiddenString

        if not widget_fn:
            widget_fn = self.schema_type_mapping.get(
                schema_fragment.get('type'))

        if not widget_fn:
            if schema_fragment.get('allOf'):
                # When the schema contains allOf in the keys, we handle it as
                # an object type.
                widget_fn = self.schema_title_mapping.get(
                    schema_fragment.get('allOf')[0].get('title'))
                if not widget_fn:
                    widget_fn = self.schema_type_mapping.get(
                        schema_fragment.get('allOf')[0].get('type'),
                        schema_widget.UnsupportedSchema
                    )
            else:
                widget_fn = schema_widget.UnsupportedSchema

        type_widget = widget_fn(
            name, schema_fragment, fragment_data, previous_object_data,
            self, parent
        )
        self.register_type_widget_plugin(type_widget)

        return type_widget

    def fetch_plugin_widget(self, plugin_data, stage_name, extra_options=None):
        '''
        Setup the settings and return a widget from the given *plugin_data*,
        *stage_name* with the optional *extra_options*.
        '''

        plugin_name = plugin_data.get('plugin')
        widget_name = plugin_data.get('widget')

        if not widget_name:
            widget_name = plugin_name
            plugin_data['widget'] = widget_name

        plugin_type = '{}.{}'.format(self.definition_type, stage_name)

        self.logger.debug('Fetching widget : {} for plugin {}'.format(
            widget_name, plugin_name
        ))

        data = self._fetch_plugin_widget(
            plugin_data, plugin_type, widget_name, extra_options=extra_options
        )
        if not data:
            if plugin_type == 'publisher.validator':
                # We have a particular default validator for the publisher to be
                # able to enable test of each validator on publish time.
                widget_name = 'default.validator.widget'
            else:
                widget_name = 'default.widget'
            self.logger.debug(
                'Widget not found, falling back on: {}'.format(widget_name)
            )

            if not plugin_data.get('widget'):
                plugin_data['widget'] = widget_name

            data = self._fetch_plugin_widget(
                plugin_data, plugin_type, widget_name,
                extra_options=extra_options
            )
        data = data[0]

        message = data['message']
        result = data['result']
        if result:
            widget = result.get(list(result.keys())[0])
        status = data['status']

        if status == constants.EXCEPTION_STATUS:
            raise Exception(
                'Got response "{}"" while fetching:\n'
                'plugin: {}\n'
                'plugin_type: {}\n'
                'plugin_name: {}'.format(
                    message, plugin_data, plugin_type, widget_name)
            )

        if result and not isinstance(widget, BaseOptionsWidget):
            raise Exception(
                'Widget {} should inherit from {}'.format(
                    widget,
                    BaseOptionsWidget
                )
            )

        widget.status_updated.connect(self._on_widget_status_updated)
        widget.asset_changed.connect(self._on_widget_asset_changed)
        widget.asset_version_changed.connect(self._asset_version_changed)
        widget.emit_initial_state()

        self.register_widget_plugin(plugin_data, widget)

        widget.run_plugin_clicked.connect(
            partial(self.on_widget_run_plugin, plugin_data)
        )
        if widget.auto_fetch_on_init:
            widget.fetch_on_init()

        return widget

    def _fetch_plugin_widget(
            self, plugin_data, plugin_type, plugin_name, extra_options=None
    ):
        '''Retrieve the widget event with the given *plugin_data*, *plugin_type*
        and *plugin_name* with the optional *extra_options*.'''
        extra_options = extra_options or {}

        plugin_options = plugin_data.get('options', {})
        plugin_options.update(extra_options)

        name = plugin_data.get('name', 'no name provided')
        description = plugin_data.get('description', 'No description provided')

        result = None
        for host_type in reversed(self.host_connection.host_types):
            for _ui_type in reversed(self.ui_types):

                data = {
                    'pipeline': {
                        'plugin_name': plugin_name,
                        'plugin_type': plugin_type,
                        'method': 'run',
                        'category': 'plugin.widget',
                        'host_type': host_type,
                        'ui_type': _ui_type
                    },
                    'settings': {
                        'options': plugin_options,
                        'name': name,
                        'description': description,
                        'context_id': self.context_id,
                        'asset_type_name': self.asset_type_name
                    }
                }

                event = ftrack_api.event.base.Event(
                    topic=core_constants.PIPELINE_RUN_PLUGIN_TOPIC,
                    data=data
                )

                result = self.session.event_hub.publish(
                    event,
                    synchronous=True
                )

                if result:
                    return result

    def _update_widget(self, event):
        '''*event* callback to update widget with the current status/value'''
        result = event['data']['pipeline']['result']
        widget_ref = event['data']['pipeline']['widget_ref']
        status = event['data']['pipeline']['status']
        message = event['data']['pipeline']['message']
        host_id = event['data']['pipeline']['host_id']
        user_data = event['data']['pipeline'].get('user_data') or {}
        user_message = user_data.get('message')

        widget = self.widgets.get(widget_ref)
        if not widget:
            self.logger.debug(
                'Widget ref :{} not found for host_id {} ! '.format(
                    widget_ref, host_id
                )
            )
            return

        if status:
            self.logger.debug(
                'updating widget: {} Status: {}, Message: {}, User Message: {}'.format(
                    widget, status, message, user_message
                )
            )
            if user_message:
                widget.set_status(status, user_message)
            else:
                widget.set_status(status, message)
        if result:
            self.logger.debug(
                'updating widget: {} with run result {}'.format(
                    widget, result
                )
            )
            widget.set_run_result(result)

    def _listen_widget_updates(self):
        '''
        Subscribe to the
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`
        topic to call the _update_widget function when the host returns and
        answer through the same topic
        '''

        self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                core_constants.PIPELINE_CLIENT_NOTIFICATION,
                self.host_connection.id
            ),
            self._update_widget
        )

    def _on_widget_status_updated(self, status):
        '''Emits signal widget_status_updated when any widget calls the
        status_updated signal'''
        self.widget_status_updated.emit(status)

    def _on_widget_asset_changed(self, asset_name, asset_id, is_valid):
        '''Callback funtion called when asset has been modified on the widget'''
        self.widget_asset_updated.emit(asset_name, asset_id, is_valid)

    def on_widget_run_plugin(self, plugin_data, method, plugin_options):
        '''
        Called when a run button (run, fetch or any method button) is clicked
        on the widget. *plugin_data* is the current plugin definition, *method*
        is the method that has to be executed in the plugin, *plugin_options* is
        not used for now but are the current options that the plugin has.
        '''
        self.widget_run_plugin.emit(plugin_data, method)

    def register_widget_plugin(self, plugin_data, widget):
        '''register the *widget* in the given *plugin_data*'''
        uid = uuid.uuid4().hex
        self._widgets_ref[uid] = widget
        plugin_data['widget_ref'] = uid

        return uid

    def get_registered_widget_plugin(self, plugin_data):
        '''return the widget registered for the given *plugin_data*.'''
        return self._widgets_ref[plugin_data['widget_ref']]

    def register_type_widget_plugin(self, widget):
        '''regiter the *widget* in the :obj:`type_widgets_ref`'''
        uid = uuid.uuid4().hex
        self._type_widgets_ref[uid] = widget

        return uid

    def reset_type_widget_plugin(self):
        '''empty :obj:`type_widgets_ref`'''
        self._type_widgets_ref = {}

    def check_components(self):
        ''' Set the component as unavailable if it isn't available on the server'''
        if not self.components_names:
            return
        for k, v in self.type_widgets.items():
            if hasattr(v, 'accordion_widgets') and v.type == core_constants.COMPONENT:
                for widget in v.accordion_widgets:
                    if widget.title not in self.components_names:
                        widget.set_unavailable()
                    else:
                        widget.set_default_state()
            elif hasattr(v, 'tabs_names') and v.type == core_constants.COMPONENT:
                for name in list(v.tabs_names.keys()):
                    if name not in self.components_names:
                        v.tab_widget.setTabEnabled(v.tabs_names[name], False)
                    else:
                        v.tab_widget.setTabEnabled(v.tabs_names[name], True)

    def _asset_version_changed(self, version_id):
        '''Callbac funtion triggered when a asset version has changed'''
        self.version_id = version_id
        asset_version_entity = self.session.query(
            'select components '
            'from AssetVersion where id is {}'.format(version_id)
        ).first()
        if not asset_version_entity:
            return
        components = asset_version_entity['components']
        self.components_names = [component['name'] for component in components]
        self.check_components()
