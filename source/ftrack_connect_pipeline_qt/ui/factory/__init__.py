# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import copy
import logging
from functools import partial
import uuid

from Qt import QtCore, QtWidgets

import ftrack_api

from ftrack_connect_pipeline import constants as core_constants

from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget
from ftrack_connect_pipeline_qt.ui.factory.base import BaseUIWidgetObject
from ftrack_connect_pipeline_qt.ui.factory import (
    overrides as override_widgets,
    default as default_widgets,
)
from ftrack_connect_pipeline_qt.ui.factory.ui_overrides import (
    UI_OVERRIDES,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import line


class WidgetFactoryBase(QtWidgets.QWidget):
    '''Main class to build widgets from json schemas and run definitions with progress indicator'''

    widgetAssetUpdated = QtCore.Signal(
        object, object, object
    )  # Emitted when user has selected asset (open) or entered an asset name (publish)
    widgetRunPlugin = QtCore.Signal(
        object, object
    )  # Emitted when run/fetch button is clicked on plugin widget
    onQueryAssetVersionDone = QtCore.Signal(
        object
    )  # (Open) Emitted when the asset version has been queried in the background
    componentsChecked = QtCore.Signal(
        object
    )  # (Open) Emitted when components has been checked against the available components on version
    updateProgressWidget = QtCore.Signal(
        object
    )  # Process async notification event

    host_types = None
    ui_types = None

    @property
    def widgets(self):
        '''Return registered plugin's widgets.'''
        return self._widgets_ref

    @property
    def host_connection(self):
        '''Return the host connection'''
        return self._host_connection

    @host_connection.setter
    def host_connection(self, host_connection):
        '''Sets :obj:`host_connection` with the given *host_connection*'''
        self._host_connection = host_connection

    @property
    def batch_id(self):
        '''Return the id of the current batch item/version'''
        return self._batch_id

    @batch_id.setter
    def batch_id(self, value):
        '''(Batch) Set the current ID of the current batch item/version'''
        self._batch_id = value

    @property
    def definition(self):
        '''Return the current working definition'''
        return self._definition

    @definition.setter
    def definition(self, value):
        '''Sets the current working definition to the given *value*'''
        self._definition = value

    def __init__(self, event_manager, ui_types, parent=None):
        '''Initialise widget factory

        *event_manager* :class:`ftrack_connect_pipeline.event.EventManager` instance

        *ui_types* List of valid ux libraries.

        '''
        super(WidgetFactoryBase, self).__init__(parent=parent)

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.session = event_manager.session
        self._event_manager = event_manager
        self.ui_types = ui_types
        self._widgets_ref = {}
        self._step_objs_ref = {}
        self._stage_objs_ref = {}
        self.context_id = None
        self.asset_type_name = None
        self._host_connection = None
        self._definition = None
        self.components_obj = None
        self.progress_widget = None
        self._batch_id = None
        self._subscriber_id = None
        self.has_error = False

        #  Load; the available components of current version
        self.components = None

        self.onQueryAssetVersionDone.connect(self.check_components)
        self.updateProgressWidget.connect(self._update_progress_widget)

    def set_context(self, context_id, asset_type_name):
        '''Set :obj:`context_id` and :obj:`asset_type_name` with the given
        *context_id* and *asset_type_name*'''
        self.context_id = context_id
        self.asset_type_name = asset_type_name

    def set_definition_type(self, definition_type):
        '''Set :obj:`definition_type` with the given *definition_type*'''
        self.definition_type = definition_type

    def get_override(
        self, step_override_name, widget_type, name, data, client_type
    ):
        '''
        From the given *step_override_name* and *widget_type* find the widget override
        '''
        obj_override = UI_OVERRIDES.get(step_override_name).get(
            '{}.{}'.format(widget_type, name), qt_constants.NOT_SET
        )
        if obj_override == qt_constants.NOT_SET:
            obj_override = UI_OVERRIDES.get(step_override_name).get(
                '{}.{}'.format(widget_type, data['type']), qt_constants.NOT_SET
            )
        if obj_override == qt_constants.NOT_SET:
            obj_override = UI_OVERRIDES.get(step_override_name).get(
                '{}.{}'.format(widget_type, client_type), qt_constants.NOT_SET
            )
        if obj_override == qt_constants.NOT_SET:
            obj_override = UI_OVERRIDES.get(step_override_name).get(
                widget_type
            )
        if obj_override and obj_override != qt_constants.NOT_SET:
            return obj_override(name, data)
        return obj_override

    @staticmethod
    def create_progress_widget(client_type, parent=None):
        '''Create progress widget for the given *client_type*. Check for overrides
        of the main widget, otherwise call the default one'''
        client_key = 'progress_widget.{}'.format(client_type)
        if client_type and client_key in UI_OVERRIDES:
            return UI_OVERRIDES.get(client_key)(None, None, parent=parent)
        else:
            return UI_OVERRIDES.get('progress_widget')(
                None, None, parent=parent
            )

    def create_main_widget(self):
        '''
        Return the main widget
        '''
        return UI_OVERRIDES.get('main_widget')(None, None)

    @staticmethod
    def client_type():
        '''Return the client type (opener, loader, publisher) for this factory.
        Must be implemented by child factory'''
        raise NotImplementedError()

    def create_step_container_widget(
        self,
        definition,
        step_type_name,
        stage_name_filters=None,
        component_names_filter=None,
        extensions_filter=None,
    ):
        '''
        Main loop to create the widgets UI overrides from schema *definition*
        based on *step_type_name* and optional *stage_name_filters*. Pass
        on *component_names_filter* and *extensions_filter* as options to the
        widget to enable filtering on context.
        '''
        step_container_obj = self.get_override(
            step_type_name,
            'step_container',
            step_type_name,
            definition,
            self.client_type(),
        )
        has_visible_plugins = False
        for step in definition[step_type_name]:
            # Create widget for the step (a component, a finaliser...)
            step_category = step['category']
            step_type = step['type']
            step_name = step.get('name')
            step_visible = step.get('visible', True) is True
            if (
                self.progress_widget
                and step_type != core_constants.FINALIZER
                and step_visible
            ):
                self.progress_widget.add_step(step_type, step_name)
            step_obj = self.get_override(
                step_type_name,
                '{}_widget'.format(step_category),
                step_name,
                step,
                self.client_type(),
            )
            if step_obj:
                self.register_object(step, step_obj, step_category)
            has_visible_stage = False
            for stage in step.get_all(category=core_constants.STAGE):
                # create widget for the stages (collector, validator, exporter/importer)
                stage_category = stage['category']
                stage_type = stage['type']
                stage_name = stage.get('name')
                if stage_name_filters and stage_name not in stage_name_filters:
                    continue
                stage_visible = stage.get('visible', True) is True
                if (
                    self.progress_widget
                    and step_type == core_constants.FINALIZER
                    and (
                        stage_name == core_constants.FINALIZER or stage_visible
                    )
                ):
                    # Add stage as a progress step for finalisers
                    self.progress_widget.add_step(
                        step_type,
                        stage_name,
                        label=UI_OVERRIDES.get(core_constants.FINALIZERS).get(
                            'progress.label.{}'.format(self.client_type())
                        ),
                    )
                stage_obj = self.get_override(
                    step_type_name,
                    '{}_widget'.format(stage_category),
                    stage_name,
                    stage,
                    self.client_type(),
                )
                if stage_obj:
                    self.register_object(stage, stage_obj, stage_category)

                has_visible_plugin = False
                for plugin in stage.get_all(category=core_constants.PLUGIN):
                    # create widget for the plugins, usually just one
                    plugin_type = plugin['type']
                    plugin_category = plugin['category']
                    plugin_name = plugin.get('name')

                    plugin_visible = plugin.get('visible', True) is True
                    if plugin_visible:
                        has_visible_plugin = True

                    plugin_container_obj = self.get_override(
                        step_type_name,
                        '{}_container'.format(plugin_category),
                        plugin_name,
                        plugin,
                        self.client_type(),
                    )
                    # Here is where we inject the user custom widgets, provide filters if supplied
                    extra_options = {'_filters': {}}
                    if extensions_filter:
                        extra_options['_filters'][
                            'file_types'
                        ] = extensions_filter
                    if component_names_filter:
                        extra_options['_filters'][
                            'component_names'
                        ] = component_names_filter

                    plugin_widget = self.fetch_plugin_widget(
                        plugin,
                        stage['name'],
                        extra_options=extra_options,
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
                    if isinstance(
                        step_obj,
                        override_widgets.PublisherAccordionStepWidgetObject,
                    ):
                        if stage_type == core_constants.COLLECTOR:
                            # Connect input change to accordion
                            # TODO: support multiple collectors
                            plugin_widget.inputChanged.connect(
                                step_obj.collector_input_changed
                            )
                            # Eventual initial summary is lost prior to the signal
                            # connect, have widget do it again
                            plugin_widget.report_input()
                        elif stage_type == core_constants.EXPORTER:
                            step_obj.set_output_plugin_name(plugin_name)

                if isinstance(
                    step_obj,
                    override_widgets.PublisherAccordionStepWidgetObject,
                ):
                    # Put validators and options in overlay
                    if stage_type == core_constants.VALIDATOR:
                        step_obj.parent_validator(stage_obj)
                        continue
                    elif stage_type == core_constants.EXPORTER:
                        step_obj.parent_exporter(stage_obj)
                        continue
                if step_obj:
                    step_obj.parent_widget(stage_obj)
                elif step_container_obj:
                    step_container_obj.parent_widget(stage_obj)
                if stage_visible and has_visible_plugin:
                    has_visible_stage = True
            if step_container_obj and step_obj:
                step_container_obj.parent_widget(step_obj)
            if step_visible and has_visible_stage:
                has_visible_plugins = True
        return step_container_obj, has_visible_plugins

    def build(
        self, definition, component_names_filter, component_extensions_filter
    ):
        '''
        Given the provided *definition* and *component_names_filter*, build the main client UI.
        '''
        self.progress_widget.prepare_add_steps()
        # Backup the original definition, as it will be extended by the user UI
        self.definition = definition

        # Create the main UI widget based on the user overrides
        main_obj = self.create_main_widget()

        # Create the context widget based on the definition and user overrides
        (
            self.context_obj,
            unused_has_visible_context_plugins,
        ) = self.create_step_container_widget(
            definition,
            core_constants.CONTEXTS,
            component_names_filter=component_names_filter,
            extensions_filter=component_extensions_filter,
        )

        # Create the components widget based on the definition
        (
            self.components_obj,
            unused_has_visible_component_plugins,
        ) = self.create_step_container_widget(
            definition,
            core_constants.COMPONENTS,
            stage_name_filters=component_names_filter,
        )

        # Create the finalizers widget based on the definition
        (
            self.finalizers_obj,
            has_visible_finalizer_plugins,
        ) = self.create_step_container_widget(
            definition, core_constants.FINALIZERS
        )

        main_obj.widget.layout().addWidget(self.context_obj.widget)

        main_obj.widget.layout().addWidget(line.Line())

        self.components_section = QtWidgets.QWidget()
        self.components_section.setLayout(QtWidgets.QVBoxLayout())
        if definition['type'] == core_constants.PUBLISHER:
            l_components_header = QtWidgets.QLabel('Components')
        else:
            l_components_header = QtWidgets.QLabel(
                'Choose which component to open'
            )
            l_components_header.setObjectName('gray')
        self.components_section.layout().addWidget(l_components_header)
        self.components_section.layout().addWidget(self.components_obj.widget)
        if definition['type'] == core_constants.LOADER:
            self.components_section.hide()
        main_obj.widget.layout().addWidget(self.components_section)

        self.finalizers_section = QtWidgets.QWidget()
        self.finalizers_section.setLayout(QtWidgets.QVBoxLayout())
        l_finalizers_header = QtWidgets.QLabel('Finalizers')
        self.finalizers_section.layout().addWidget(l_finalizers_header)
        self.finalizers_section.layout().addWidget(self.finalizers_obj.widget)
        show_finalisers = has_visible_finalizer_plugins
        if (
            show_finalisers
            and definition['type'] == core_constants.LOADER
            or not UI_OVERRIDES.get(core_constants.FINALIZERS).get(
                'show', True
            )
        ):
            show_finalisers = False

        if not show_finalisers:
            self.finalizers_section.hide()

        main_obj.widget.layout().addWidget(self.finalizers_section)

        main_obj.widget.layout().addStretch()

        self.progress_widget.widgets_added()

        # Check all components status of the current UI
        self.post_build()

        return main_obj.widget

    def post_build(self):
        '''Post build actions'''
        self.update_selected_components(True)
        for step in self.definition[core_constants.COMPONENTS]:
            step_obj = self.get_registered_object(step, step['category'])
            if isinstance(step_obj, default_widgets.DefaultStepWidgetObject):
                step_obj.check_box.stateChanged.connect(
                    self.update_selected_components
                )

    def update_selected_components(self, state):
        '''Go through components and calculate amount of enabled components and totals'''
        enabled_components = 0
        total_components = 0
        for step in self.definition[core_constants.COMPONENTS]:
            step_obj = self.get_registered_object(step, step['category'])
            if isinstance(step_obj, BaseUIWidgetObject):
                enabled = step_obj.enabled
                if enabled:
                    enabled_components += 1
            else:
                self.logger.error(
                    "{} isn't instance of BaseUIWidgetObject".format(step_obj)
                )
            total_components += 1
        if isinstance(
            self.components_obj,
            override_widgets.AccordionStepContainerWidgetObject,
        ):
            self.components_obj.update_selected_components(
                enabled_components, total_components
            )

    def fetch_plugin_widget(self, plugin_data, stage_name, extra_options=None):
        '''
        Setup the settings and return a widget from the given *plugin_data*,
        *stage_name* with the optional *extra_options*.
        '''

        plugin_name = plugin_data.get(core_constants.PLUGIN)
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
                widget_name = 'common_default_shared_validator'
            else:
                widget_name = 'common_default_shared'
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
        if not data:
            raise Exception("common_default_shared widget is not reachable")
        data = data[0]

        message = data['message']
        result = data['result']
        if result:
            widget = result.get(list(result.keys())[0])
        status = data['status']

        if status == core_constants.EXCEPTION_STATUS:
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

        widget.assetVersionChanged.connect(
            self._asset_version_changed
        )  # Open/load
        widget.assetChanged.connect(self._on_widget_asset_changed)

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

    def _update_progress_widget_async(self, event):
        self.updateProgressWidget.emit(event)

    def _update_progress_widget(self, event):
        '''Update the progress widget based on the client progress notification *event* emitted during run'''
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
            step_name if step_type != core_constants.FINALIZER else stage_name
        )

        if status == core_constants.RUNNING_STATUS:
            status_message = "Running Stage {}... ({}/{})".format(
                stage_name, current_plugin_index, total_plugins
            )
            self.progress_widget.update_step_status(
                step_type,
                step_name_effective,
                status,
                status_message,
                results,
                self._batch_id,
            )
        elif status == core_constants.ERROR_STATUS:
            status_message = "Failed"
            self.progress_widget.update_step_status(
                step_type,
                step_name_effective,
                status,
                status_message,
                results,
                self._batch_id,
            )
            self.has_error = True
        elif status == core_constants.SUCCESS_STATUS:
            status_message = "Completed"
            self.progress_widget.update_step_status(
                step_type,
                step_name_effective,
                status,
                status_message,
                results,
                self._batch_id,
            )

    def update_widget(self, log_item):
        '''Callback to update widget with the current status/value provided with *log_item*'''
        if not log_item.widget_ref:
            self.logger.debug(
                'No widget_ref on the log item. log_item: {}'.format(log_item)
            )
            return
        widget = self.widgets.get(log_item.widget_ref)
        if not widget:
            self.logger.debug(
                'Widget ref :{} not found for host_id {} ! '.format(
                    log_item.widget_ref, log_item.host_id
                )
            )
            return

        if log_item.status:
            self.logger.debug(
                'updating widget: {} Status: {}, Message: {}, User Message: {}'.format(
                    widget,
                    log_item.status,
                    log_item.message,
                    log_item.user_message,
                )
            )
            if log_item.user_message:
                widget.set_status(log_item.status, log_item.user_message)
            else:
                widget.set_status(log_item.status, log_item.message)

        if log_item.result:
            self.logger.debug(
                'updating widget: {} with run result {}'.format(
                    widget, log_item.result
                )
            )
            widget.set_run_result(log_item.result)

    def listen_widget_updates(self):
        '''
        Subscribe to the
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_CLIENT_PROGRESS_NOTIFICATION`
        topic to call the _update_progress_widget function when the host returns and
        answer through the same topic
        '''

        self._subscriber_id = self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                core_constants.PIPELINE_CLIENT_PROGRESS_NOTIFICATION,
                self.host_connection.id,
            ),
            self._update_progress_widget_async,
        )
        self.has_error = False

    def end_widget_updates(self):
        '''Unsubscribe from :const:`~ftrack_connnect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`'''
        if self._subscriber_id:
            self.session.event_hub.unsubscribe(self._subscriber_id)

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
        '''Register base UI widgget object *obj* based on *type* and also store in JSON *data*'''
        if type == core_constants.STAGE:
            self._stage_objs_ref[obj.widget_id] = obj
        if type == core_constants.STEP:
            self._step_objs_ref[obj.widget_id] = obj
        data['widget_ref'] = obj.widget_id
        return obj.widget_id

    def get_registered_widget_plugin(self, plugin_data):
        '''Return the widget registered for the given *plugin_data*'''
        if plugin_data.get('widget_ref'):
            return self._widgets_ref[plugin_data['widget_ref']]

    def get_registered_object(self, data, category):
        '''Return the widget registered for the given *plugin_data*'''
        if data.get('widget_ref'):
            if category == core_constants.STAGE:
                return self._stage_objs_ref[data['widget_ref']]
            if category == core_constants.STEP:
                return self._step_objs_ref[data['widget_ref']]

    def query_asset_version_from_version_id(self, version_id):
        '''Retreive asset version from ftrack based on its *version_id*'''
        asset_version_entity = self.session.query(
            'select components, components.name '
            'from AssetVersion where id is {}'.format(version_id)
        ).first()
        return asset_version_entity

    def _query_asset_version_callback(self, asset_version_entity):
        '''Callback upon asset version ftrack query'''
        if asset_version_entity:
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
        self.onQueryAssetVersionDone.emit(asset_version_entity)

    def _asset_version_changed(self, version_id):
        '''Callback function triggered when a asset version has changed'''
        if version_id is None:
            # No asset available to open/load
            self._query_asset_version_callback(None)
            return
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
        '''Serialize factorized UI back into a JSON object, taking user options into account'''
        out = self.definition
        for step in out.get_all(category=core_constants.STEP):
            step_obj = self.get_registered_object(step, step['category'])
            for stage in step.get_all(category=core_constants.STAGE):
                stage_obj = self.get_registered_object(
                    stage, stage['category']
                )
                for plugin in stage.get_all(category=core_constants.PLUGIN):
                    plugin_widget = self.get_registered_widget_plugin(plugin)
                    if plugin_widget:
                        plugin.update(plugin_widget.to_json_object())
                if stage_obj:
                    stage.update(stage_obj.to_json_object())
            if step_obj:
                step.update(step_obj.to_json_object())

        return out


class OpenerAssemblerWidgetFactoryBase(WidgetFactoryBase):
    '''Shared factory base between opener and assembler'''

    def __init__(self, event_manager, ui_types, parent=None):
        super(OpenerAssemblerWidgetFactoryBase, self).__init__(
            event_manager, ui_types, parent=parent
        )

    def check_components(self, asset_version_entity):
        '''(Override)'''
        if not self.components or asset_version_entity is None:
            return
        available_components = 0
        try:
            for step in self.definition[core_constants.COMPONENTS]:
                step_obj = self.get_registered_object(step, step['category'])
                if not isinstance(
                    step_obj, default_widgets.DefaultStepWidgetObject
                ) and not isinstance(
                    step_obj, override_widgets.RadioButtonStepWidgetObject
                ):
                    self.logger.error(
                        "{} should be instance of DefaultStepWidgetObject ".format(
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
                override_widgets.RadioButtonStepContainerWidgetObject,
            ):
                self.components_obj.pre_select()
        finally:
            self.componentsChecked.emit(available_components)
