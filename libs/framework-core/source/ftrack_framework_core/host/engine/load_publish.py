# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
import ftrack_api
import copy

from ftrack_framework_core import constants
from ftrack_framework_core.host.engine import BaseEngine


# TODO: try to separate engine to its own library, like the definitions.
# TODO: engines should be cfreated dependeant on the workflow of the schema, so this engine is for loader, publisher etc... but not for AM or resolver.
class LoadPublishEngine(BaseEngine):
    '''
    Base engine class.
    '''

    engine_type = [constants.LOADER, constants.OPENER, constants.PUBLISHER]
    '''Engine type for this engine class'''

    # TODO: double check if we really need to declare the init here.
    def __init__(
            self, event_manager, ftrack_object_manager, host_types, host_id,
            asset_type_name
    ):
        '''
        Initialise HostConnection with instance of
        :class:`~ftrack_framework_core.event.EventManager` , and *host*,
        *host_id* and *asset_type_name*

        *host* : Host type.. (ex: python, maya, nuke....)
        *host_id* : Host id.
        *asset_type_name* : If engine is initialized to publish or load, the asset
        type should be specified.
        '''
        super(LoadPublishEngine, self).__init__(
            event_manager, ftrack_object_manager, host_types, host_id,
            asset_type_name
        )


    def run_plugin(
        self,
        plugin_definition,
        plugin_options=None,
        plugin_data=None,
        plugin_context_data=None,
        plugin_method='run',
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

        plugin_name = plugin_definition['plugin']
        plugin_default_method = plugin_definition['default_method']

        plugin_result_data=None

        for host_type in reversed(self._host_types):
            # TODO: double check that it syncronously returns us the result of the plugin.
            #  Should be the plugin_info dictionary-
            plugin_result_data = self.event_manager.publish.execute_plugin(
                plugin_name, plugin_default_method, plugin_method, host_type, plugin_data,
                plugin_options, plugin_context_data
            )

        return plugin_result_data

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

        i = 1
        for plugin_definition in plugins:
            plugin_name = plugin_definition['plugin']
            plugin_enabled = plugin_definition['enabled']

            if not plugin_enabled:
                self.logger.debug(
                    'Skipping plugin {} as it has been disabled'.format(
                        plugin_name
                    )
                )
                continue

            # TODO: clean up this and provide a definition_info dictionary like
            #  we do with the plugins. Probably the definition_object should be
            #  the one that has the definition info? or maybe just the engine.
            self.event_manager.publish.notify_definition_progress_client(
                host_id=self.host_id,
                step_type=step_type,
                step_name=step_name,
                stage_name=stage_name,
                total_plugins=len(plugins),
                current_plugin_index=i,
                status=constants.RUNNING_STATUS,
                results=None,
            )

            result = None
            plugin_options = plugin_definition['options']
            # Update the plugin_options with the stage_options.
            plugin_options.update(stage_options)
            category = plugin_definition['category']
            type = plugin_definition['type']
            default_method = plugin_definition['default_method']

            plugin_result = self.run_plugin(
                plugin_definition,
                # We don't want to pass the information of the previous plugin, so that
                # is why we only pass the data of the previous stage.
                plugin_data=stage_data,
                # From the definition + stage_options
                plugin_options=plugin_options,
                # Data from the plugin context
                plugin_context_data=stage_context,
                # default_method is defined in the definitions
                plugin_method=plugin_definition['default_method'],
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

            # TODO: This should be the plugin result becasue its already the plugin_info dictionary returned by the plugin.
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
        # TODO: should this come from constants as well?
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

                # TODO: this should also be defined in constants
                stage_dict = {
                    "name": stage_name,
                    "result": stage_result,
                    "status": stage_status,
                    "category": category,
                    "type": type,
                }

                step_results.append(stage_dict)

                status = constants.SUCCESS_STATUS
                # We stop the loop if the stage failed. To raise an error on
                # run_definitions
                if not step_status:
                    status = constants.ERROR_STATUS

                self.event_manager.publish.notify_definition_progress_client(
                    host_id=self.host_id,
                    step_type=step_type,
                    step_name=step_name,
                    stage_name=stage_name,
                    total_plugins=None,
                    current_plugin_index=None,
                    status=constants.ERROR_STATUS,
                    results=step_results,
                )

                bool_status = constants.status_bool_mapping[status]
                if not bool_status:
                    return step_status, step_results

        self.event_manager.publish.notify_definition_progress_client(
            host_id=self.host_id,
            step_type=step_type,
            step_name=step_name,
            stage_name=None,
            total_plugins=None,
            current_plugin_index=None,
            status=constants.SUCCESS_STATUS,
            results=step_results,
        )
        return step_status, step_results

    # TODO: as a low priority task, try to improve this makeing a better use of the definition object, maybe extending the definition object as well to know how to run steps, stages and plugins.
    # TODO: receive definition in here instead of data
    def run_definition(self, definition_data):
        '''
        Runs the whole definition from the provided *data*.
        Call the method :meth:`run_step` for each context, component and
        finalizer steps.

        *data* : pipeline['data'] provided from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run` Should be a
        valid definition.
        '''
        # TODO: we should use definition object in here to clean this up
        context_data = None
        components_output = []
        finalizers_output = []
        for step_group in constants.STEP_GROUPS:
            group_steps = definition_data[step_group]
            group_results = []

            if step_group == constants.FINALIZERS:
                group_results = copy.deepcopy(components_output)

            group_status = True

            for step in group_steps:
                # TODO: bare in mind that this is a definitionObject, so we can make use of it like step.name
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

                # TODO: this should be defined in constnats
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
                            # TODO: re-evaluate this kind of things, what if the
                            #  definition doesn't have exporters?
                            #  Example: the AM definition. Can't we make use of
                            #  the definition object to solve this kind of stuff?
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
