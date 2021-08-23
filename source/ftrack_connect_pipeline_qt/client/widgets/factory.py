# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import copy
import logging
from collections import OrderedDict
from functools import partial

import uuid
import ftrack_api
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.client_ui_overrides import UI_OVERRIDES

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
        self._step_objs_ref = {}
        self._stage_objs_ref = {}
        self._type_widgets_ref = {}
        self.context_id = None
        self.asset_type_name = None
        self.host_connection = None
        self.original_definition = None
        self.working_definition = None

        self.components_names = []

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

    def get_override(self, type_name, widget_type, name, data):
        obj_override = UI_OVERRIDES.get(
            type_name
        ).get('{}.{}'.format(widget_type, name))
        if not obj_override:
            obj_override = UI_OVERRIDES.get(
                type_name
            ).get(widget_type)
        if obj_override:
            return obj_override(name, data)
        return obj_override

    def create_main_widget(self):
        # Check for overrides of the main widget, otherwise call the default one
        return UI_OVERRIDES.get('main_widget')(None, None)

    # TODO: Choose between this or create typed widget
    #  In case to choose this recursive method, make sure that is 100% working
    #  and is all parenting as it should without errors, also, make sure it's working with multiple plugins
    def recursive_typed_widget(self, definition, parent_type, type_list, parent=None):
        for definition_obj in definition[type_list[0]]:
            category = definition_obj['category']
            name = definition_obj.get('name')

            if category == 'plugin':
                plugin_container_obj = self.get_override(
                    parent_type, '{}_container'.format(category), name, definition_obj
                )
                plugin_widget = self.fetch_plugin_widget(
                    definition_obj, parent.name
                )

                obj = plugin_widget

                if plugin_container_obj:
                    plugin_widget.toggle_status(show=False)
                    plugin_widget.toggle_name(show=False)
                    plugin_container_obj.parent_widget(plugin_widget)
                    obj = plugin_container_obj

            else:
                obj = self.get_override(
                    parent_type, '{}_widget'.format(category), name, definition_obj
                )
                if obj:
                    self.register_object(definition_obj, obj, category)
                else:
                    obj = parent

            if len(type_list) > 1:
                self.recursive_typed_widget(
                    definition_obj,
                    parent_type,
                    type_list[1:],
                    obj
                )
            if parent:
                parent.parent_widget(obj)
    # TODO: Choose between this or create typed widget
    #  In case to choose this recursive method, make sure that is 100% working
    #  and is all parenting as it should without errors, also, make sure it's working with multiple plugins
    def create_typed_widget_recursive(self, definition, type_name):

        step_container_obj = self.get_override(
            type_name, 'step_container', type_name, definition
        )

        self.recursive_typed_widget(
            definition,
            type_name,
            [type_name, 'stages','plugins'],
            step_container_obj
        )
        return step_container_obj

    def create_typed_widget(self, definition, type_name):

        step_container_obj = self.get_override(
            type_name, 'step_container', type_name, definition
        )

        for step in definition[type_name]:
            # Create widget for the step
            # print(step)
            step_category = step['category']
            step_name = step.get('name')
            step_obj = self.get_override(
                type_name, '{}_widget'.format(step_category), step_name, step
            )
            if step_obj:
                self.register_object(step, step_obj, step_category)
            for stage in step['stages']:
                # create widget for the stages
                # print(stage)
                stage_category = stage['category']
                stage_name = stage.get('name')
                stage_obj = self.get_override(
                    type_name, '{}_widget'.format(stage_category), stage_name, stage
                )
                if stage_obj:
                    self.register_object(stage, stage_obj, stage_category)
                for plugin in stage['plugins']:
                    # create widget for the plugins
                    # print(plugin)
                    plugin_category = plugin['category']
                    plugin_name = plugin.get('name')
                    plugin_container_obj = self.get_override(
                        type_name, '{}_container'.format(plugin_category), plugin_name, plugin
                    )
                    plugin_widget = self.fetch_plugin_widget(
                        plugin, stage['name']
                    )
                    if plugin_container_obj:
                        plugin_widget.toggle_status(show=False)
                        plugin_widget.toggle_name(show=False)
                        plugin_container_obj.parent_widget(plugin_widget)
                        stage_obj.parent_widget(plugin_container_obj)
                    else:
                        stage_obj.parent_widget(plugin_widget)
                if step_obj:
                    step_obj.parent_widget(stage_obj)
                elif step_container_obj:
                    step_container_obj.parent_widget(stage_obj)
            if step_container_obj and step_obj:
                step_container_obj.parent_widget(step_obj)
        return step_container_obj

    def build_definition_ui(self, name, definition=None):
        self.original_definition = copy.deepcopy(definition)
        self.working_definition = definition

        main_obj = self.create_main_widget()

        context_obj = self.create_typed_widget(
            definition, type_name=core_constants.CONTEXTS
        )

        components_obj = self.create_typed_widget(
            definition, type_name=core_constants.COMPONENTS
        )

        finalizers_obj = None
        if UI_OVERRIDES.get(core_constants.FINALIZERS).get('show', True):
            finalizers_obj = self.create_typed_widget(
                definition, type_name=core_constants.FINALIZERS
            )

        main_obj.widget.layout().addWidget(context_obj.widget)
        main_obj.widget.layout().addWidget(components_obj.widget)
        if finalizers_obj:
            main_obj.widget.layout().addWidget(finalizers_obj.widget)

        return main_obj.widget

    def to_json_object(self):
        out = self.working_definition
        types = [core_constants.CONTEXTS,core_constants.COMPONENTS, core_constants.FINALIZERS]
        for type_name in types:
            for step in out[type_name]:
                step_obj = self.get_registered_object(step, step['category'])
                for stage in step['stages']:
                    stage_obj = self.get_registered_object(stage, stage['category'])
                    for plugin in stage['plugins']:
                        plugin_widget = self.get_registered_widget_plugin(plugin)
                        if plugin_widget:
                            plugin.update(plugin_widget.to_json_object())
                    if stage_obj:
                        stage.update(stage_obj.to_json_object())
                if step_obj:
                    step.update(step_obj.to_json_object())

        return out


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
        # widget.emit_initial_state()

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

    def register_object(self, data, obj, type):
        if type == 'stage':
            self._stage_objs_ref[obj.widget_id] = obj
        if type == 'step':
            self._step_objs_ref[obj.widget_id] = obj
        data['widget_ref'] = obj.widget_id
        return obj.widget_id

    def get_registered_widget_plugin(self, plugin_data):
        '''return the widget registered for the given *plugin_data*.'''
        if plugin_data.get('widget_ref'):
            return self._widgets_ref[plugin_data['widget_ref']]

    def get_registered_object(self, data, category):
        '''return the widget registered for the given *plugin_data*.'''
        if data.get('widget_ref'):
            if category == 'stage':
                return self._stage_objs_ref[data['widget_ref']]
            if category == 'step':
                return self._step_objs_ref[data['widget_ref']]


    def reset_type_widget_plugin(self):
        '''empty :obj:`type_widgets_ref`'''
        self._type_widgets_ref = {}

    # TODO: Review this method, not sure is working since the refactor
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
            'select components, components.name '
            'from AssetVersion where id is {}'.format(version_id)
        ).first()
        if not asset_version_entity:
            return
        components = asset_version_entity['components']
        self.components_names = [component['name'] for component in components]
        self.check_components()
