# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import ftrack_api
import copy

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.log.log_item import LogItem
from ftrack_connect_pipeline.asset import FtrackObjectManager
from ftrack_connect_pipeline.asset.dcc_object import DccObject


def getEngine(baseClass, engineType):
    '''
    Returns the Class or Subclass of the given *baseClass* that matches the
    name of the given *engineType*
    '''
    for subclass in baseClass.__subclasses__():
        if engineType == subclass.__name__:
            return subclass
        match = getEngine(subclass, engineType)
        if match:
            return match


class BaseEngine(object):
    '''
    Base engine class.
    '''

    engine_type = 'base'
    '''Engine type for this engine class'''

    FtrackObjectManager = FtrackObjectManager
    '''FtrackObjectManager class to use'''
    DccObject = DccObject
    '''DccObject class to use'''

    @property
    def ftrack_object_manager(self):
        '''
        Initializes and returns an instance of
        :class:`~ftrack_connect_pipeline.asset.FtrackObjectManager`
        '''
        if not isinstance(
            self._ftrack_object_manager, self.FtrackObjectManager
        ):
            self._ftrack_object_manager = self.FtrackObjectManager(
                self.event_manager
            )
        return self._ftrack_object_manager

    @property
    def dcc_object(self):
        '''
        Returns the :obj:`dcc_object` from the
        :class:`~ftrack_connect_pipeline.asset.FtrackObjectManager`
        '''
        return self.ftrack_object_manager.dcc_object

    @dcc_object.setter
    def dcc_object(self, value):
        '''
        Sets the :obj:`dcc_object` to the
        :class:`~ftrack_connect_pipeline.asset.FtrackObjectManager`
        '''
        self.ftrack_object_manager.dcc_object = value

    @property
    def asset_info(self):
        '''
        Returns the :obj:`asset_info` from the
        :class:`~ftrack_connect_pipeline.asset.FtrackObjectManager`
        '''
        return self.ftrack_object_manager.asset_info

    @asset_info.setter
    def asset_info(self, value):
        '''
        Sets the :obj:`asset_info` to the
        :class:`~ftrack_connect_pipeline.asset.FtrackObjectManager`
        '''
        self.ftrack_object_manager.asset_info = value

    @property
    def host_id(self):
        '''Returns the current host id.'''
        return self._host_id

    @property
    def host_types(self):
        '''Return the current host type.'''
        return self._host_types

    def __init__(self, event_manager, host_types, host_id, asset_type_name):
        '''
        Initialise HostConnection with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager` , and *host*,
        *host_id* and *asset_type_name*

        *host* : Host type.. (ex: python, maya, nuke....)
        *host_id* : Host id.
        *asset_type_name* : If engine is initialized to publish or load, the asset
        type should be specified.
        '''
        super(BaseEngine, self).__init__()

        self.asset_type_name = asset_type_name
        self.session = event_manager.session
        self._host_types = host_types
        self._host_id = host_id
        self._definition = None
        self._ftrack_object_manager = None

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.event_manager = event_manager

    def run_event(
        self,
        plugin_name,
        plugin_type,
        host_type,
        data,
        options,
        context_data,
        method,
    ):
        '''
        Returns an :class:`ftrack_api.event.base.Event` with the topic
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_RUN_PLUGIN_TOPIC`
        with the data of the given *plugin_name*, *plugin_type*,
        *host_definition*, *data*, *options*, *context_data*, *method*

        *plugin_name* : Name of the plugin.

        *plugin_type* : Type of plugin.

        *host_definition* : Host type.

        *data* : data to pass to the plugin.

        *options* : options to pass to the plugin

        *context_data* : result of the context plugin containing the context_id,
        aset_name... Or None

        *method* : Method of the plugin to be executed.

        '''
        return ftrack_api.event.base.Event(
            topic=constants.PIPELINE_RUN_PLUGIN_TOPIC,
            data={
                'pipeline': {
                    'plugin_name': plugin_name,
                    'plugin_type': plugin_type,
                    'method': method,
                    'category': 'plugin',
                    'host_type': host_type,
                    'definition': self._definition['name']
                    if self._definition
                    else None,
                },
                'settings': {
                    'data': data,
                    'options': options,
                    'context_data': context_data,
                },
            },
        )

    def _run_plugin(
        self,
        plugin,
        plugin_type,
        options=None,
        data=None,
        context_data=None,
        method='run',
    ):
        '''
        Returns the result of running the plugin with the event returned from
        :meth:`run_event` using the given *plugin*, *plugin_type*,
        *options*, *data*, *context_data*, *method*

        *plugin* : Plugin definition, a dictionary with the plugin information.

        *plugin_type* : Type of plugin.


        *options* : options to pass to the plugin

        *data* : data to pass to the plugin.

        *context_data* : result of the context plugin containing the context_id,
        aset_name... Or None

        *method* : Method of the plugin to be executed.

        '''

        plugin_name = plugin['plugin']
        start_data = {
            'plugin_name': plugin_name,
            'plugin_type': plugin_type,
            'method': method,
            'status': constants.RUNNING_STATUS,
            'result': None,
            'execution_time': 0,
            'message': None,
        }

        self._notify_client(plugin, start_data)

        result_data = copy.deepcopy(start_data)
        result_data['status'] = constants.UNKNOWN_STATUS

        for host_type in reversed(self._host_types):

            event = self.run_event(
                plugin_name,
                plugin_type,
                host_type,
                data,
                options,
                context_data,
                method,
            )

            plugin_result_data = self.session.event_hub.publish(
                event, synchronous=True
            )
            if plugin_result_data:
                result_data = plugin_result_data[0]
                break

        self._notify_client(plugin, result_data)
        return result_data

    def _notify_client(self, plugin, result_data):
        '''
        Publish an :class:`ftrack_api.event.base.Event` with the topic
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`
        to notify the client of the given *plugin* result *result_data*.
        Also store plugin result in persistent database.

        *plugin* : Plugin definition, a dictionary with the plugin information.

        *result_data* : Result of the plugin execution.

        '''

        result_data['host_id'] = self.host_id
        if plugin:
            result_data['widget_ref'] = plugin.get('widget_ref')
            result_data["plugin_id"] = plugin.get('plugin_id')
        else:
            result_data['widget_ref'] = None
            result_data["plugin_id"] = None

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_CLIENT_NOTIFICATION,
            data={'pipeline': result_data},
        )

        self.event_manager.publish(
            event,
        )

    def run(self, data):
        '''
        Executes the :meth:`_run_plugin` with the provided *data*.
        Returns the result of the mentioned method.

        *data* : pipeline['data'] provided from the client host connection at
        :meth:`~ftrack_connect_pipeline.client.HostConnection.run`
        '''

        method = data.get('method', 'run')
        plugin = data.get('plugin', None)
        plugin_type = data.get('plugin_type', None)

        result = None

        if plugin:
            plugin_result = self._run_plugin(
                plugin,
                plugin_type,
                data=plugin.get('plugin_data'),
                options=plugin['options'],
                context_data=None,
                method=method,
            )
            status = plugin_result['status']
            bool_status = constants.status_bool_mapping[status]
            result = plugin_result
            if not bool_status:
                raise Exception(
                    'An error occurred during the execution of the plugin {}'
                    '\n status: {} \n result: {}'.format(
                        plugin['plugin'], status, result
                    )
                )

        return result

    # Base functions for loader, opener and publisher

    def run_stage(
        self,
        stage_name,
        plugins,
        stage_context,
        stage_options,
        stage_data,
        plugins_order=None,
        step_type=None,
        step_name=None,
    ):
        '''
        Returns the bool status and the result list of dictionaries of executing
        all the plugins in the stage.
        This function executes all the defined plugins for this stage using
        the :meth:`_run_plugin`

        *stage_name* : Name of the stage that's executing.

        *plugins* : List of plugins that has to execute.

        *stage_context* : Context dictionary with the result of the context
        plugin containing the context_id, aset_name... Or None

        *stage_options* : Options dictionary to be passed to each plugin.

        *stage_data* : Data list of dictionaries to be passed to each stage.

        *plugins_order* : Order of the plugins to be executed.

        *step_type* : Type of the step.
        '''
        plugin_type = '{}.{}'.format(self.engine_type, stage_name)

        stage_status = True
        stage_results = []

        # We don't want to pass the information of the previous plugin, so that
        # is why we only pass the data of the previous stage.
        data = stage_data

        i = 1
        for plugin in plugins:

            plugin_name = plugin['plugin']
            plugin_enabled = plugin['enabled']

            if not plugin_enabled:
                self.logger.debug(
                    'Skipping plugin {} as it has been disabled'.format(
                        plugin_name
                    )
                )
                continue

            self._notify_progress_client(
                step_type=step_type,
                step_name=step_name,
                stage_name=stage_name,
                total_plugins=len(plugins),
                current_plugin_index=i,
                status=constants.RUNNING_STATUS,
                results=None,
            )

            result = None
            plugin_options = plugin['options']
            # Update the plugin_options with the stage_options.
            plugin_options.update(stage_options)
            category = plugin['category']
            type = plugin['type']
            default_method = plugin['default_method']

            plugin_result = self._run_plugin(
                plugin,
                plugin_type,
                data=data,
                options=plugin_options,
                context_data=stage_context,
                method=default_method,
            )

            bool_status = constants.status_bool_mapping[
                plugin_result['status']
            ]
            if not bool_status:
                stage_status = False
                result = plugin_result['result']
                # We log a warning if a plugin on the stage failed.
                self.logger.error(
                    "Execution of the plugin {} failed.".format(plugin_name)
                )
            else:
                if plugin_result['result']:
                    result = plugin_result['result'].get(default_method)
                    if step_type == constants.CONTEXT:
                        result['asset_type_name'] = self.asset_type_name

            plugin_dict = {
                "name": plugin_name,
                "options": plugin_options,
                "result": result,
                "status": bool_status,
                "category": category,
                "type": type,
                "plugin_type": plugin_result['plugin_type'],
                "method": plugin_result['method'],
                "user_data": plugin_result.get('user_data') or {},
                "message": plugin_result['message'],
                "widget_ref": plugin_result['widget_ref'],
                "host_id": plugin_result['host_id'],
                "plugin_id": plugin_result['plugin_id'],
            }

            stage_results.append(plugin_dict)
            i += 1
        return stage_status, stage_results

    def run_step(
        self,
        step_name,
        stages,
        step_context,
        step_options,
        step_data,
        stages_order,
        step_type,
    ):
        '''
        Returns the bool status and the result list of dictionaries of executing
        all the stages in the step.
        This function executes all the defined stages for for this step using
        the :meth:`run_stage` with the given *stage_order*.

        *step_name* : Name of the step that's executing.

        *stages* : List of stages that has to execute.

        *step_context* : Context dictionary with the result of the context
        plugin containing the context_id, aset_name... Or None

        *step_options* : Options dictionary to be passed to each stage.

        *step_data* : Data list of dictionaries to be passed to each stage.

        *stages_order* : Order of the stages to be executed.

        *step_type* : Type of the step.
        '''

        step_status = True
        step_results = []

        # data will be, the previous step data, plus the current step dictionary
        # plus the stage result filled on every loop
        data = step_data
        current_step_dict = {
            "name": step_name,
            "result": step_results,
            "type": step_type,
        }
        data.append(current_step_dict)

        for stage in stages:
            for stage_name in stages_order:
                if stage_name != stage['name']:
                    continue

                stage_enabled = stage['enabled']
                stage_plugins = stage['plugins']
                category = stage['category']
                type = stage['type']

                if not stage_plugins:
                    continue

                if not stage_enabled:
                    self.logger.debug(
                        'Skipping stage {} as it has been disabled'.format(
                            stage_name
                        )
                    )
                    continue

                stage_status, stage_result = self.run_stage(
                    stage_name=stage_name,
                    plugins=stage_plugins,
                    stage_context=step_context,
                    stage_options=step_options,
                    stage_data=data,
                    plugins_order=None,
                    step_type=step_type,
                    step_name=step_name,
                )
                if not stage_status:
                    step_status = False
                    # Log an error if the execution of a stage has failed.
                    self.logger.error(
                        "Execution of the stage {} failed.".format(stage_name)
                    )

                stage_dict = {
                    "name": stage_name,
                    "result": stage_result,
                    "status": stage_status,
                    "category": category,
                    "type": type,
                }

                step_results.append(stage_dict)

                # We stop the loop if the stage failed. To raise an error on
                # run_definitions
                if not step_status:
                    self._notify_progress_client(
                        step_type,
                        step_name,
                        stage_name,
                        None,
                        None,
                        constants.ERROR_STATUS,
                        step_results,
                    )
                    return step_status, step_results
                else:
                    self._notify_progress_client(
                        step_type,
                        step_name,
                        stage_name,
                        None,
                        None,
                        constants.SUCCESS_STATUS,
                        step_results,
                    )
        self._notify_progress_client(
            step_type,
            step_name,
            None,
            None,
            None,
            constants.SUCCESS_STATUS,
            step_results,
        )
        return step_status, step_results

    def _notify_progress_client(
        self,
        step_type,
        step_name,
        stage_name,
        total_plugins,
        current_plugin_index,
        status,
        results,
    ):
        '''
        Publish an :class:`ftrack_api.event.base.Event` with the topic
        :const:`~ftrack_connnect_pipeline.constants.PIPELINE_CLIENT_NOTIFICATION`
        to notify the client of the given *plugin* result *result_data*.
        Also store plugin result in persistent database.

        *plugin* : Plugin definition, a dictionary with the plugin information.

        *result_data* : Result of the plugin execution.

        '''

        data = {
            'host_id': self.host_id,
            'step_type': step_type,
            'step_name': step_name,
            'stage_name': stage_name,
            'total_plugins': total_plugins,
            'current_plugin_index': current_plugin_index,
            'status': status,
            'results': results,
        }

        event = ftrack_api.event.base.Event(
            topic=constants.PIPELINE_CLIENT_PROGRESS_NOTIFICATION,
            data={'pipeline': data},
        )

        self.event_manager.publish(
            event,
        )

    def run_definition(self, data):
        '''
        Runs the whole definition from the provided *data*.
        Call the method :meth:`run_step` for each context, component and
        finalizer steps.

        *data* : pipeline['data'] provided from the client host connection at
        :meth:`~ftrack_connect_pipeline.client.HostConnection.run` Should be a
        valid definition.
        '''

        self._definition = data

        context_data = None
        components_output = []
        finalizers_output = []
        for step_group in constants.STEP_GROUPS:
            group_steps = data[step_group]
            group_results = []

            if step_group == constants.FINALIZERS:
                group_results = copy.deepcopy(components_output)

            group_status = True

            for step in group_steps:
                step_name = step['name']
                step_stages = step['stages']
                step_enabled = step['enabled']
                step_stage_order = step['stage_order']
                step_category = step['category']
                step_type = step['type']
                step_options = {}

                if step_group == constants.COMPONENTS:
                    if 'file_formats' in step:
                        step_options['file_formats'] = step[
                            'file_formats'
                        ]  # Pass on to collector

                if not step_enabled:
                    self.logger.debug(
                        'Skipping step {} as it has been disabled'.format(
                            step_name
                        )
                    )
                    continue

                step_data = copy.deepcopy(group_results)

                step_status, step_result = self.run_step(
                    step_name=step_name,
                    stages=step_stages,
                    step_context=context_data,
                    step_options=step_options,
                    step_data=step_data,
                    stages_order=step_stage_order,
                    step_type=step_type,
                )

                if not step_status:
                    group_status = False
                    # Log an error if the execution of a step has failed.
                    self.logger.error(
                        "Execution of the step {} failed.".format(step_name)
                    )

                step_dict = {
                    "name": step_name,
                    "result": step_result,
                    "status": step_status,
                    "category": step_category,
                    "type": step_type,
                }

                group_results.append(step_dict)
                # Stop if context results are false to raise a proper error.
                if not group_status:
                    break

            if not group_status:
                raise Exception(
                    'An error occurred during the execution of the a {} and '
                    'can not continue, please, check the plugin logs'.format(
                        step_group
                    )
                )

            if step_group == constants.CONTEXTS:
                context_latest_step = group_results[-1]
                context_latest_stage = context_latest_step.get('result')[-1]
                context_data = {}
                for context_plugin in context_latest_stage.get('result'):
                    context_data.update(context_plugin.get('result'))

            elif step_group == constants.COMPONENTS:
                components_output = copy.deepcopy(group_results)
                i = 0
                for component_step in group_results:
                    for component_stage in component_step.get("result"):
                        self.logger.debug(
                            "Checking stage name {} of type {}".format(
                                component_stage.get("name"),
                                component_stage.get("type"),
                            )
                        )
                        if not component_stage.get("type") in [
                            constants.IMPORTER,
                            constants.EXPORTER,
                            constants.POST_IMPORTER,
                        ]:
                            self.logger.debug(
                                "Removing stage name {} of type {}".format(
                                    component_stage.get("name"),
                                    component_stage.get("type"),
                                )
                            )
                            components_output[i]['result'].remove(
                                component_stage
                            )
                    i += 1
            elif step_group == constants.FINALIZERS:
                finalizers_output = group_results

        return finalizers_output


from ftrack_connect_pipeline.host.engine.publish import *
from ftrack_connect_pipeline.host.engine.load import *
from ftrack_connect_pipeline.host.engine.open import *
from ftrack_connect_pipeline.host.engine.asset_manager import *
