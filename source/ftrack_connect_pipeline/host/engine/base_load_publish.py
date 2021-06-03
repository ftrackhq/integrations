# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import copy
import logging
import ftrack_api
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline.host.engine import BaseEngine


class BaseLoaderPublisherEngine(BaseEngine):
    '''
    Base Loader and Publisher Engine class.
    '''
    engine_type = 'loader_publisher'
    '''Engine type for this engine class'''

    def __init__(self, event_manager, host_types, host_id, asset_type):
        '''
        Initialise HostConnection with instance of
        :class:`~ftrack_connect_pipeline.event.EventManager` , and *host*,
        *host_id* and *asset_type*

        *host* : Host type.. (ex: python, maya, nuke....)

        *host_id* : Host id.

        *asset_type* : Asset type should be specified.
        '''
        super(BaseLoaderPublisherEngine, self).__init__(
            event_manager, host_types, host_id, asset_type
        )

    def run_stage(
            self, stage_name, plugins, stage_context, stage_options, stage_data,
            plugins_order=None, step_type=None
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

        for plugin in plugins:
            result = None
            plugin_name = plugin['plugin']
            plugin_options = plugin['options']
            # Update the plugin_options with the stage_options.
            plugin_options.update(stage_options)
            category = plugin['category']
            type = plugin['type']
            default_method = plugin['default_method']

            plugin_result = self._run_plugin(
                plugin, plugin_type,
                data=data,
                options=plugin_options,
                context_data=stage_context,
                method=default_method
            )

            bool_status = constants.status_bool_mapping[plugin_result['status']]
            if not bool_status:
                stage_status = False
                result = plugin_result['result']
                # We log a warning if a plugin on the stage failed.
                self.logger.error(
                    "Execution of the plugin {} failed.".format(plugin_name)
                )
            else:
                result = plugin_result['result'].get(default_method)
                if step_type == constants.CONTEXT:
                    result['asset_type'] = self.asset_type

            plugin_dict = {
                "name": plugin_name,
                "result": result,
                "status": bool_status,
                "category": category,
                "type": type,
                "plugin_type": plugin_result['plugin_type'],
                "method": plugin_result['method'],
                "user_data": plugin_result.get('user_data') or {}
            }

            stage_results.append(plugin_dict)
        return stage_status, stage_results


    def run_step(
            self, step_name, stages, step_context, step_options, step_data,
            stages_order, step_type
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
            "type": step_type
        }
        data.append(current_step_dict)


        for stage in stages:
            for stage_name in stages_order:
                if stage_name != stage['name']:
                    continue

                stage_plugins = stage['plugins']
                category = stage['category']
                type = stage['type']

                if not stage_plugins:
                    continue

                stage_status, stage_result = self.run_stage(
                    stage_name=stage_name,
                    plugins=stage_plugins,
                    stage_context=step_context,
                    stage_options=step_options,
                    stage_data=data,
                    plugins_order=None,
                    step_type=step_type
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
                    "type": type
                }

                step_results.append(stage_dict)

                # We stop the loop if the stage failed. To raise an error on
                # run_definitions
                if not step_status:
                    return step_status, step_results

        return step_status, step_results

    def run_definition(self, data):
        '''
        Runs the whole definition from the provided *data*.
        Call the method :meth:`run_step` for each context, component and
        finalizer steps.

        *data* : pipeline['data'] provided from the client host connection at
        :meth:`~ftrack_connect_pipeline.client.HostConnection.run` Should be a
        valid definition.
        '''

        context_data = None
        components_output = []
        for step_group in constants.STEPS_ORDER:
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
                step_options = []

                if step_group == constants.COMPONENTS:
                    step_options = {'component_name': step_name}

                if not step_enabled:
                    self.logger.debug(
                        'Skipping step {} as it been disabled'.format(
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
                    step_type=step_type
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
                    "type": step_type
                }

                group_results.append(step_dict)
                #Stop if context results are false to raise a proper error.
                if not group_status:
                    break

            if not group_status:
                raise Exception(
                    'An error occurred during the execution of the a {} and '
                    'can not continue, please, check the plugin logs'.format(step_group)
                )

            if step_group == constants.CONTEXTS:
                context_latest_step = group_results[-1]
                context_latest_stage = context_latest_step.get('result')[-1]
                context_latest_plugin = context_latest_stage.get('result')[-1]
                context_latest_plugin_result = context_latest_plugin.get('result')
                context_data = context_latest_plugin_result

            elif step_group == constants.COMPONENTS:
                components_output = copy.deepcopy(group_results)
                i = 0
                for component_step in group_results:
                    for component_stage in component_step.get("result"):
                        self.logger.debug(
                            "Checking stage name {} of type {}".format(
                                component_stage.get("name"), component_stage.get("type")
                            )
                        )
                        if (
                                component_stage.get("type") != constants.OUTPUT
                                and
                                component_stage.get("type") != constants.POST_IMPORT
                        ):
                            self.logger.debug(
                                "Removing stage name {} of type {}".format(
                                    component_stage.get("name"), component_stage.get("type")
                                )
                            )
                            components_output[i]['result'].remove(component_stage)
                    i += 1

        #TODO: maybe we could be returning the finalizers_result? or maybe not
        # needed and just dd it to a log or pas it to the notify client
        return True