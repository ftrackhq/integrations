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
        self._type_widgets_ref = {}
        self.context_id = None
        self.asset_type_name = None
        self.host_connection = None

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

    def create_main_widget(self):
        # Check for overrides of the main widget, otherwise call the default one
        # TODO: move this to a separated file
        return UI_OVERRIDES.get('main_widget')(None, None)

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

    def create_typed_widget(self, fragment_data, type_name):
        step_container_obj = self.get_override(
            type_name, 'step_container', type_name, fragment_data
        )

        for step in fragment_data[type_name]:
            # Create widget for the step
            # print(step)
            step_name = step.get('name')
            step_optional = step.get('optional')

            step_obj = self.get_override(
                type_name, 'step_widget', step_name, step
            )

            for stage in step['stages']:
                # create widget for the stages
                # print(stage)
                stage_name = stage.get('name')
                stage_obj = self.get_override(
                    type_name, 'stage_widget', stage_name, stage
                )
                for plugin in stage['plugins']:
                    # create widget for the plugins
                    # print(plugin)
                    plugin_name = plugin.get('name')
                    plugin_container_obj = self.get_override(
                        type_name, 'plugin_container', plugin_name, plugin
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

    def create_widget(
            self, name, schema_fragment, fragment_data=None,
            previous_object_data=None, parent=None
    ):

        main_obj = self.create_main_widget()

        context_obj = self.create_typed_widget(
            fragment_data, type_name='contexts'
        )

        components_obj = self.create_typed_widget(
            fragment_data, type_name='components'
        )

        finalizers_obj = None
        if UI_OVERRIDES.get('finalizers').get('show', True):
            finalizers_obj = self.create_typed_widget(
                fragment_data, type_name='finalizers'
            )

        main_obj.widget.layout().addWidget(context_obj.widget)
        main_obj.widget.layout().addWidget(components_obj.widget)
        if finalizers_obj:
            main_obj.widget.layout().addWidget(finalizers_obj.widget)

        return main_obj.widget

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
