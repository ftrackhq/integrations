# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack
import copy
import logging
from functools import partial
import uuid
import json

from Qt import QtCore, QtWidgets

import ftrack_api

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline import constants as core_constants
from ftrack_connect_pipeline_qt.plugin.widgets import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.client import BaseUIWidget
from ftrack_connect_pipeline_qt.ui.client import (
    overrides as override_widgets,
    default as default_widgets,
)
from ftrack_connect_pipeline_qt.ui.client.client_ui_overrides import (
    UI_OVERRIDES,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import line


class WidgetFactoryBase(QtWidgets.QWidget):
    '''Main class to represent widgets from json schemas'''

    widgetStatusUpdated = QtCore.Signal(object)
    widgetContextUpdated = QtCore.Signal(object)
    widgetAssetUpdated = QtCore.Signal(object, object, object)
    widgetRunPlugin = QtCore.Signal(object, object)
    onQueryAssetVersionDone = QtCore.Signal(object)
    componentsChecked = QtCore.Signal(object)

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

    @property
    def host_connection(self):
        return self._host_connection

    @host_connection.setter
    def host_connection(self, host_connection):
        '''Sets :obj:`host_connection` with the given *host_connection*.'''
        self._host_connection = host_connection

    @property
    def version_id(self):
        return self._version_id

    @version_id.setter
    def version_id(self, value):
        '''(Batch) Set the current ID of the running version'''
        self._version_id = value

    def __init__(self, event_manager, ui_types, client_name):
        '''Initialise WidgetFactory with *event_manager*, *ui*

        *event_manager* should be the
        :class:`ftrack_connect_pipeline.event.EventManager` instance to
        communicate to the event server.

        *ui_types* List of valid ux libraries.

        '''
        super(WidgetFactoryBase, self).__init__()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = event_manager.session
        self._event_manager = event_manager
        self.ui_types = ui_types
        self.client_name = client_name
        self._widgets_ref = {}
        self._step_objs_ref = {}
        self._stage_objs_ref = {}
        self._type_widgets_ref = {}
        self.context_id = None
        self.asset_type_name = None
        self._host_connection = None
        self.original_definition = None
        self.working_definition = None
        self.components_obj = None
        self.progress_widget = None
        self._version_id = None
        self._subscriber_id = None
        self.has_error = False

        #  Load; the available components of current version
        self.components = None

        self.onQueryAssetVersionDone.connect(self.check_components)

    def set_context(self, context_id, asset_type_name):
        '''Set :obj:`context_id` and :obj:`asset_type_name` with the given
        *context_id* and *asset_type_name*'''
        self.context_id = context_id
        self.asset_type_name = asset_type_name

    def set_definition_type(self, definition_type):
        '''Set :obj:`definition_type` with the given *definition_type*'''
        self.definition_type = definition_type

    def get_override(self, type_name, widget_type, name, data, client_name):
        '''
        From the given *type_name* and *widget_type* find the widget override
        in the client_ui_overrides.py file
        '''
        obj_override = UI_OVERRIDES.get(type_name).get(
            '{}.{}'.format(widget_type, name), constants.NOT_SET
        )
        if obj_override == constants.NOT_SET:
            obj_override = UI_OVERRIDES.get(type_name).get(
                '{}.{}'.format(widget_type, data['type']), constants.NOT_SET
            )
        if obj_override == constants.NOT_SET:
            obj_override = UI_OVERRIDES.get(type_name).get(
                '{}.{}'.format(widget_type, client_name), constants.NOT_SET
            )
        if obj_override == constants.NOT_SET:
            obj_override = UI_OVERRIDES.get(type_name).get(widget_type)
        if obj_override and obj_override != constants.NOT_SET:
            return obj_override(name, data)
        return obj_override

    @staticmethod
    def create_progress_widget(client_name):
        # Check for overrides of the main widget, otherwise call the default one
        client_key = 'progress_widget.{}'.format(client_name)
        if client_name and client_key in UI_OVERRIDES:
            return UI_OVERRIDES.get(client_key)(None, None)
        else:
            return UI_OVERRIDES.get('progress_widget')(None, None)

    def create_main_widget(self):
        '''
        Check for overrides of the main widget,
        otherwise call the default one.
        '''
        return UI_OVERRIDES.get('main_widget')(None, None)

    def create_typed_widget(
        self, definition, type_name, stage_name_filters=None
    ):
        '''
        Main loop to create the widgets UI overrides.
        '''
        step_container_obj = self.get_override(
            type_name,
            'step_container',
            type_name,
            definition,
            self.client_name,
        )
        for step in definition[type_name]:
            # Create widget for the step (a component, a finaliser...)
            step_category = step['category']
            step_type = step['type']
            step_name = step.get('name')
            if (
                self.progress_widget
                and step_type != 'finalizer'
                and step.get('visible', True) is True
            ):
                self.progress_widget.add_component(step_type, step_name)
            step_obj = self.get_override(
                type_name,
                '{}_widget'.format(step_category),
                step_name,
                step,
                self.client_name,
            )
            if step_obj:
                self.register_object(step, step_obj, step_category)
            for stage in step['stages']:
                # create widget for the stages (collector, validator, output/importer)
                stage_category = stage['category']
                stage_type = stage['type']
                stage_name = stage.get('name')
                if stage_name_filters and stage_name not in stage_name_filters:
                    continue
                # @@@ DEBUG - skip creating dynamic widgets
                # if not isinstance(
                #    step_obj, override_widgets.PublisherAccordionStepWidget
                # ):
                #    if (
                #        stage_type == core_constants.VALIDATOR
                #        or stage_type == core_constants.OUTPUT
                #    ):
                #        continue
                if (
                    self.progress_widget
                    and step_type == 'finalizer'
                    and stage.get('visible', True) is True
                ):
                    self.progress_widget.add_component(step_type, stage_name)
                stage_obj = self.get_override(
                    type_name,
                    '{}_widget'.format(stage_category),
                    stage_name,
                    stage,
                    self.client_name,
                )
                if stage_obj:
                    self.register_object(stage, stage_obj, stage_category)

                for plugin in stage['plugins']:
                    # create widget for the plugins, usually just one
                    plugin_type = plugin['type']
                    plugin_category = plugin['category']
                    plugin_name = plugin.get('name')
                    plugin_container_obj = self.get_override(
                        type_name,
                        '{}_container'.format(plugin_category),
                        plugin_name,
                        plugin,
                        self.client_name,
                    )
                    # Here is where we inject the user custom widgets.
                    plugin_widget = self.fetch_plugin_widget(
                        plugin, stage['name']
                    )
                    # Start parenting widgets
                    if plugin_container_obj:
                        plugin_widget.toggle_status(show=False)
                        plugin_widget.toggle_name(show=False)
                        plugin_container_obj.parent_widget(plugin_widget)
                        stage_obj.parent_widget(
                            plugin_container_obj, add_line=True
                        )
                    else:
                        stage_obj.parent_widget(plugin_widget)
                    if stage_type == core_constants.COLLECTOR and isinstance(
                        step_obj, override_widgets.PublisherAccordionStepWidget
                    ):
                        # Connect input change to accordion
                        # TODO: support multiple collectors
                        plugin_widget.inputChanged.connect(
                            step_obj.collector_input_changed
                        )
                        # Eventual initial summary is lost prior to the signal connect, have widget do it again
                        plugin_widget.report_input()

                if isinstance(
                    step_obj, override_widgets.PublisherAccordionStepWidget
                ):
                    # Put validators and options in overlay
                    if stage_type == core_constants.VALIDATOR:
                        step_obj.parent_validator(stage_obj)
                        continue
                    elif stage_type == core_constants.OUTPUT:
                        step_obj.parent_output(stage_obj)
                        continue
                if step_obj:
                    step_obj.parent_widget(stage_obj)
                elif step_container_obj:
                    step_container_obj.parent_widget(stage_obj)
            if step_container_obj and step_obj:
                step_container_obj.parent_widget(step_obj)
        return step_container_obj

    def build_definition_ui(self, definition, component_names_filter):
        '''
        Given the provided definition, we generate the client UI.
        '''
        self.progress_widget.prepare_add_components()
        # Backup the original definition, as it will be extended by the user UI
        self.original_definition = copy.deepcopy(definition)
        self.working_definition = definition

        # Create the main UI widget based on the user overrides
        main_obj = self.create_main_widget()

        # Create the context widget based on the definition ans user overrides
        self.context_obj = self.create_typed_widget(
            definition, type_name=core_constants.CONTEXTS
        )

        # Create the components widget based on the definition
        self.components_obj = self.create_typed_widget(
            definition,
            type_name=core_constants.COMPONENTS,
            stage_name_filters=component_names_filter,
        )

        # Create the finalizers widget based on the definition
        self.finalizers_obj = self.create_typed_widget(
            definition, type_name=core_constants.FINALIZERS
        )

        main_obj.widget.layout().addWidget(self.context_obj.widget)

        main_obj.widget.layout().addWidget(line.Line())

        self.components_section = QtWidgets.QWidget()
        self.components_section.setLayout(QtWidgets.QVBoxLayout())
        self.components_section.layout().addWidget(
            QtWidgets.QLabel(
                'Components'
                if definition['type'] == core_constants.PUBLISHER
                else 'Choose which component to open'
            )
        )
        self.components_section.layout().addWidget(self.components_obj.widget)
        if definition['type'] == core_constants.LOADER:
            self.components_section.hide()
        main_obj.widget.layout().addWidget(self.components_section)

        self.finalizers_section = QtWidgets.QWidget()
        self.finalizers_section.setLayout(QtWidgets.QVBoxLayout())
        self.finalizers_section.layout().addWidget(
            QtWidgets.QLabel('Finalizers')
        )
        self.finalizers_section.layout().addWidget(self.finalizers_obj.widget)
        if definition['type'] == core_constants.LOADER or not UI_OVERRIDES.get(
            core_constants.FINALIZERS
        ).get('show', True):
            self.finalizers_section.hide()
        main_obj.widget.layout().addWidget(self.finalizers_section)

        main_obj.widget.layout().addStretch()

        self.progress_widget.components_added()

        # Check all components status of the current UI
        self.post_build_definition()

        return main_obj.widget

    def post_build_definition(self):
        self.check_components(None)
        self.update_selected_components(True)
        for step in self.working_definition[core_constants.COMPONENTS]:
            step_obj = self.get_registered_object(step, step['category'])
            if isinstance(step_obj, default_widgets.DefaultStepWidget):
                step_obj.check_box.stateChanged.connect(
                    self.update_selected_components
                )

    def update_selected_components(self, state):
        enabled_components = 0
        total_components = 0
        for step in self.working_definition[core_constants.COMPONENTS]:
            step_obj = self.get_registered_object(step, step['category'])
            if isinstance(step_obj, BaseUIWidget):
                enabled = step_obj.is_enabled
                if enabled:
                    enabled_components += 1
            else:
                self.logger.error(
                    "{} isn't instance of BaseUIWidget".format(step_obj)
                )
            total_components += 1
        if isinstance(
            self.components_obj, override_widgets.AccordionStepContainerWidget
        ):
            self.components_obj.update_selected_components(
                enabled_components, total_components
            )

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

        self.logger.debug(
            'Fetching widget : {} for plugin {}'.format(
                widget_name, plugin_name
            )
        )

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
                plugin_data,
                plugin_type,
                widget_name,
                extra_options=extra_options,
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
                    message, plugin_data, plugin_type, widget_name
                )
            )

        if result and not isinstance(widget, BaseOptionsWidget):
            raise Exception(
                'Widget {} should inherit from {}'.format(
                    widget, BaseOptionsWidget
                )
            )

        widget.statusUpdated.connect(self._on_widget_status_updated)
        widget.assetVersionChanged.connect(self._asset_version_changed)  # Load
        widget.assetChanged.connect(self._on_widget_asset_changed)  # Publish

        self.register_widget_plugin(plugin_data, widget)

        widget.runPluginClicked.connect(
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
                        'ui_type': _ui_type,
                    },
                    'settings': {
                        'options': plugin_options,
                        'name': name,
                        'description': description,
                        'context_id': self.context_id,
                        'asset_type_name': self.asset_type_name,
                    },
                }

                event = ftrack_api.event.base.Event(
                    topic=core_constants.PIPELINE_RUN_PLUGIN_TOPIC, data=data
                )

                result = self.session.event_hub.publish(
                    event, synchronous=True
                )

                if result:
                    return result

    def _update_progress_widget(self, event):
        step_type = event['data']['pipeline']['step_type']
        step_name = event['data']['pipeline']['step_name']
        stage_name = event['data']['pipeline']['stage_name']
        total_plugins = event['data']['pipeline']['total_plugins']
        current_plugin_index = event['data']['pipeline'][
            'current_plugin_index'
        ]
        status = event['data']['pipeline']['status']
        results = event['data']['pipeline']['results']

        step_name_effective = (
            step_name if step_type != 'finalizer' else stage_name
        )

        if status == constants.RUNNING_STATUS:
            status_message = "Running Stage {}... ({}/{})".format(
                stage_name, current_plugin_index, total_plugins
            )
            self.progress_widget.update_component_status(
                step_type,
                step_name_effective,
                status,
                status_message,
                results,
                self._version_id,
            )
        elif status == constants.ERROR_STATUS:
            status_message = "Failed"
            self.progress_widget.update_component_status(
                step_type,
                step_name_effective,
                status,
                status_message,
                results,
                self._version_id,
            )
            self.has_error = True
        elif status == constants.SUCCESS_STATUS:
            status_message = "Completed"
            self.progress_widget.update_component_status(
                step_type,
                step_name_effective,
                status,
                status_message,
                results,
                self._version_id,
            )

    # def update_widget(self, log_item):
    #     '''*event* callback to update widget with the current status/value'''
    #     if not log_item.widget_ref:
    #         self.logger.debug(
    #             'No widget_ref on the log item. log_item: {}'.format(log_item)
    #         )
    #         return
    #     widget = self.widgets.get(log_item.widget_ref)
    #     if not widget:
    #         self.logger.debug(
    #             'Widget ref :{} not found for host_id {} ! '.format(
    #                 log_item.widget_ref, log_item.host_id
    #             )
    #         )
    #         return
    #
    #     if log_item.status:
    #         self.logger.debug(
    #             'updating widget: {} Status: {}, Message: {}, User Message: {}'.format(
    #                 widget,
    #                 log_item.status,
    #                 log_item.message,
    #                 log_item.user_message,
    #             )
    #         )
    #         if log_item.user_message:
    #             widget.set_status(log_item.status, log_item.user_message)
    #         else:
    #             widget.set_status(log_item.status, log_item.message)
    #
    #     if log_item.result:
    #         self.logger.debug(
    #             'updating widget: {} with run result {}'.format(
    #                 widget, log_item.result
    #             )
    #         )
    #         widget.set_run_result(log_item.result)

    def listen_widget_updates(self):
        '''
        Subscribe to the
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`
        topic to call the _update_widget function when the host returns and
        answer through the same topic
        '''

        self._subscriber_id = self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                core_constants.PIPELINE_CLIENT_PROGRESS_NOTIFICATION,
                self.host_connection.id,
            ),
            self._update_progress_widget,
        )
        self.has_error = False

    def end_widget_updates(self):
        '''Unsubscribe from :const:`~ftrack_connnect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`'''
        if self._subscriber_id:
            self.session.event_hub.unsubscribe(self._subscriber_id)

    def _on_widget_status_updated(self, status):
        '''Emits signal widget_status_updated when any widget calls the
        status_updated signal'''
        self.widgetStatusUpdated.emit(status)

    def _on_widget_asset_changed(self, asset_name, asset_id, is_valid):
        '''Callback function called when asset has been modified on the widget'''
        self.widgetAssetUpdated.emit(asset_name, asset_id, is_valid)

    def on_widget_run_plugin(self, plugin_data, method, plugin_options):
        '''
        Called when a run button (run, fetch or any method button) is clicked
        on the widget. *plugin_data* is the current plugin definition, *method*
        is the method that has to be executed in the plugin, *plugin_options* is
        not used for now but are the current options that the plugin has.
        '''
        self.widgetRunPlugin.emit(plugin_data, method)

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

    def query_asset_version_from_version_id(self, version_id):
        asset_version_entity = self.session.query(
            'select components, components.name '
            'from AssetVersion where id is {}'.format(version_id)
        ).first()
        return asset_version_entity

    def _query_asset_version_callback(self, asset_version_entity):
        if not asset_version_entity:
            self.onQueryAssetVersionDone.emit(None)
            return
        components = asset_version_entity['components']
        self.components = components
        self.onQueryAssetVersionDone.emit(asset_version_entity)
        self.components_section.show()
        # If there is a Finalizer widget show the widget otherwise not.
        if (
            UI_OVERRIDES.get(core_constants.FINALIZERS).get('show', True)
            is True
        ):
            self.finalizers_section.show()

    def _asset_version_changed(self, version_id):
        '''Callback function triggered when a asset version has changed'''
        # self.version_id = version_id

        thread = BaseThread(
            name='get_asset_version_entity_thread',
            target=self.query_asset_version_from_version_id,
            callback=self._query_asset_version_callback,
            target_args=[version_id],
        )
        thread.start()

    def check_components(self, asset_version_entity):
        '''Set the component as unavailable if it isn't available on the server'''
        raise NotImplementedError()

    def to_json_object(self):
        out = self.working_definition
        types = [
            core_constants.CONTEXTS,
            core_constants.COMPONENTS,
            core_constants.FINALIZERS,
        ]
        for type_name in types:
            for step in out[type_name]:
                step_obj = self.get_registered_object(step, step['category'])
                for stage in step['stages']:
                    stage_obj = self.get_registered_object(
                        stage, stage['category']
                    )
                    for plugin in stage['plugins']:
                        plugin_widget = self.get_registered_widget_plugin(
                            plugin
                        )
                        if plugin_widget:
                            plugin.update(plugin_widget.to_json_object())
                    if stage_obj:
                        stage.update(stage_obj.to_json_object())
                if step_obj:
                    step.update(step_obj.to_json_object())

        return out


class LoaderWidgetFactory(WidgetFactoryBase):
    def __init__(self, event_manager, ui_types, client_name):
        super(LoaderWidgetFactory, self).__init__(
            event_manager, ui_types, client_name
        )

    def check_components(self, asset_version_entity):
        import traceback

        print(traceback.print_stack())
        available_components = 0
        try:
            if not self.components or asset_version_entity is None:
                return
            for step in self.working_definition[core_constants.COMPONENTS]:
                step_obj = self.get_registered_object(step, step['category'])
                if not isinstance(
                    step_obj, default_widgets.DefaultStepWidget
                ) and not isinstance(
                    step_obj, override_widgets.RadioButtonItemStepWidget
                ):
                    self.logger.error(
                        "{} should be instance of DefaultStepWidget ".format(
                            step_obj.name
                        )
                    )
                    continue
                file_formats = None
                if step_obj.check_components(
                    self.session, self.components, file_formats=file_formats
                ):
                    available_components += 1
            if isinstance(
                self.components_obj,
                override_widgets.RadioButtonStepContainerWidget,
            ):
                self.components_obj.pre_select()
        finally:
            self.componentsChecked.emit(available_components)


class OpenerWidgetFactory(LoaderWidgetFactory):
    def __init__(self, event_manager, ui_types, client_name):
        super(OpenerWidgetFactory, self).__init__(
            event_manager, ui_types, client_name
        )
        self.progress_widget = self.create_progress_widget(self.client_name)


class ImporterWidgetFactory(LoaderWidgetFactory):
    '''Augmented widget factory for importer/assembler'''

    def __init__(self, event_manager, ui_types):
        super(ImporterWidgetFactory, self).__init__(
            event_manager, ui_types, 'assembler'
        )

    def set_definition(self, definition):
        self.working_definition = definition

    def build_definition_ui(self, main_widget):
        '''Based on the given definition, build options widget. Assume that
        definition has been set in advance.'''
        self.logger.debug(
            'build_definition_ui() working_definition: {}'.format(
                json.dumps(self.working_definition, indent=4)
            )
        )

        # Backup the original definition, as it will be extended by the user UI
        self.original_definition = copy.deepcopy(self.working_definition)

        # Create the components widget based on the definition
        self.components_obj = self.create_typed_widget(
            self.working_definition,
            type_name=core_constants.COMPONENTS,
        )

        # Create the finalizers widget based on the definition
        self.finalizers_obj = self.create_typed_widget(
            self.working_definition, type_name=core_constants.FINALIZERS
        )

        main_widget.layout().addWidget(self.components_obj.widget)

        finalizers_label = QtWidgets.QLabel('Finalizers')
        main_widget.layout().addWidget(finalizers_label)
        finalizers_label.setObjectName('h4')

        main_widget.layout().addWidget(self.finalizers_obj.widget)

        if not UI_OVERRIDES.get(core_constants.FINALIZERS).get('show', True):
            self.finalizers_obj.hide()

        main_widget.layout().addStretch()

        # Check all components status of the current UI
        self.post_build_definition()

        return main_widget

    def build_progress_ui(self, component):
        '''Build only progress widget components, prepare to run.'''

        types = [
            core_constants.CONTEXTS,
            core_constants.COMPONENTS,
            core_constants.FINALIZERS,
        ]

        for type_name in types:
            for step in self.working_definition[type_name]:
                step_type = step['type']
                step_name = step.get('name')
                if (
                    self.progress_widget
                    and step_type != 'finalizer'
                    and step.get('visible', True) is True
                ):
                    self.progress_widget.add_component(
                        step_type,
                        step_name,
                        version_id=component['version']['id'],
                    )
                step_obj = self.get_registered_object(step, step['category'])
                for stage in step['stages']:
                    stage_name = stage.get('name')
                    if (
                        self.progress_widget
                        and step_type == 'finalizer'
                        and stage.get('visible', True) is True
                    ):
                        self.progress_widget.add_component(
                            step_type,
                            stage_name,
                            version_id=component['version']['id'],
                        )

    def check_components(self, asset_version_entity):
        if not self.components:
            # Wait for version to be selected and loaded
            return
        super(OpenerWidgetFactory, self).check_components(asset_version_entity)


class PublisherWidgetFactory(WidgetFactoryBase):
    def __init__(self, event_manager, ui_types, client_name):
        super(PublisherWidgetFactory, self).__init__(
            event_manager, ui_types, client_name
        )
        self.progress_widget = self.create_progress_widget(self.client_name)

    def check_components(self, unused_asset_version_entity):
        available_components = 0
        try:
            if self.working_definition:
                available_components = len(
                    self.working_definition[core_constants.COMPONENTS]
                )
        finally:
            self.componentsChecked.emit(available_components)
