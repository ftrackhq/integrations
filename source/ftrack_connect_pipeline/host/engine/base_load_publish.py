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

    def run_context(self, context_stage):
        '''
        Returns the :const:`~ftrack_connnect_pipeline.constants.status` and the
        result of executing the plugins of the given *context_stage* with the
        :meth:`_run_plugin`

        *context_stage* : Context stage of dictionary of a valid definition.
        '''
        statuses = []
        results = {}

        stage_name = context_stage['name']
        plugin_type = '{}.{}'.format(self.engine_type, stage_name)
        for plugin in context_stage['plugins']:
            result = None
            asset_name = plugin['options'].get('asset_name')
            if not asset_name:
                result = "Asset name isn't valid"
                status = constants.ERROR_STATUS
            else:
                status, method_result = self._run_plugin(
                    plugin, plugin_type,
                    options=plugin['options']
                )
                if method_result:
                    result = method_result.get(list(method_result.keys())[0])

            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                raise Exception(
                    'An error occurred during the execution of the context '
                    'plugin {}\n stage: {} \n status: {} \n result: {}'.format(
                        plugin['plugin'], stage_name, status, result)
                )

            statuses.append(bool_status)
            results.update(result)

        return statuses, results

    def run_component(
            self, component_name, component_stages, context_data, stages_order
    ):
        '''
        Returns the :const:`~ftrack_connnect_pipeline.constants.status` and the
        result of executing the plugins with the :meth:`_run_plugin` of the
        given *component_stages* of the given  *component_name* with the
        given *stages_order* and the given *context_data*

        *component_name* : Component name where we are working on

        *component_stages* : Stages of the component name. (Collector,
        validator...)

        *context_data* : Data returned from the execution of the context plugin.

        *stages_order* : Order of the *component_stages* to be executed
        '''

        results = {}
        statuses = {}

        for component_stage in component_stages:
            for stage_name in stages_order:
                if stage_name != component_stage['name']:
                    continue

                plugins = component_stage['plugins']

                if not plugins:
                    continue

                plugin_type = '{}.{}'.format(self.engine_type, stage_name)

                collected_data = results.get(constants.COLLECTOR, [])
                stages_result = []
                stage_status = []

                for plugin in plugins:
                    result = None
                    plugin_options = plugin['options']
                    plugin_options['component_name'] = component_name
                    status, method_result = self._run_plugin(
                        plugin, plugin_type,
                        data=collected_data,
                        options=plugin_options,
                        context=context_data
                    )
                    if method_result:
                        result = method_result.get(list(method_result.keys())[0])
                    bool_status = constants.status_bool_mapping[status]
                    stage_status.append(bool_status)
                    if isinstance(result, list):
                        stages_result.extend(result)
                    else:
                        stages_result.append(result)
                    if not bool_status:
                        self.logger.error(
                            'An error occurred during the execution of the '
                            'component plugin {} \n status: {} \n '
                            'result: {}'.format(
                                plugin['plugin'], status, result
                            )
                        )

                results[stage_name] = stages_result
                statuses[stage_name] = all(stage_status)
                if not statuses[stage_name]:
                    raise Exception(
                        'An error occurred during the execution of '
                        'the stage {} \n status: {} \n result: {}'.format(
                            stage_name, statuses[stage_name], results[stage_name]
                        )
                    )

        return statuses, results

    def run_finalizer(self, finalizer_stage, finalizer_data, context_data):
        '''
        Returns the :const:`~ftrack_connnect_pipeline.constants.status` and the
        result of executing the plugins with the :meth:`_run_plugin` of the
        given *finalizer_stage* with the given *finalizer_data* and the
        given *context_data*

        *finalizer_stage* : Finalizer stage Name (finalizer)

        *finalizer_data* : Collected data from the execution of the output stage
        or post_import stage of the previously executed components.

        *context_data* : Data returned from the execution of the context plugin.
        '''
        statuses = []
        results = []

        stage_name = finalizer_stage['name']
        plugin_type = '{}.{}'.format(self.engine_type, stage_name)
        for plugin in finalizer_stage['plugins']:
            result = None
            status, method_result = self._run_plugin(
                plugin, plugin_type,
                data=finalizer_data,
                options=plugin['options'],
                context=context_data
            )
            if method_result:
                result = method_result.get(list(method_result.keys())[0])
            bool_status = constants.status_bool_mapping[status]
            if not bool_status:
                raise Exception(
                    'An error occurred during the execution of the finalizer '
                    'plugin {}\n stage: {} \n status: {} \n result: {}'.format(
                        plugin['plugin'], stage_name, status, result)
                )
            statuses.append(bool_status)
            results.append(result)

        return statuses, results

    def run_stage(
            self, stage_name, plugins, stage_context, stage_options, stage_data,
            plugins_order=None, step_type=None
    ):
        #TODO: Check if the step_context description is correct,
        # is it a list or a dictionary?
        '''
        Returns the bool status and the result list dictionary of executing all
        the plugins in the stage.
        This function executes all the defined plugins for this stage using
        the :meth:`_run_plugin`

        *stage_name* : Name of the stage that's executing.

        *plugins* : List of plugins that has to execute.

        *stage_context* : Context list with the dictionary with the context
        where it has to be executed.

        *stage_options* : Options dictionary to be passed to each plugin.

        *stage_data* : Data list of dictionaries to be passed to each stage.

        *plugins_order* : Order of the stages to be executed.

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
            # We update the plugin_options with the stage_options.
            # This solves things like: plugin_options['component_name'] = step_name
            plugin_options.update(stage_options)
            #TODO: plugin category and plugin type have to be updated to match steps and stages
            category = plugin['type']#plugin['category']
            type = plugin['plugin_type']#plugin['type']

            plugin_status, plugin_result = self._run_plugin(
                plugin, plugin_type,
                # TODO: to get the collected data, We should modify the base of
                #  the validator and output/postimport plugin to check in the
                #  data if there is a collected data and pas it to the data in
                #  the plugin Done. Missing test
                data=data,#collected_data,
                options=plugin_options,
                context=stage_context,
                method="run"
            )

            if plugin_result:
                # TODO: we could add the run_method key to the definitions and
                #  get this default or run methon from there
                result = plugin_result.get("run")
                # TODO: we should be saing if step_type == contexts or
                #  parent == contexts or try to add this in the base context plugin
                if step_type == "context": # Or should be type contexts in plural? think about it and change it in caseconstants.CONTEXTS:
                    result['asset_type'] = self.asset_type
            bool_status = constants.status_bool_mapping[plugin_status]
            if not bool_status:
                stage_status = False

            plugin_dict = {
                "name": plugin_name,
                "result": result,
                "status": bool_status,
                "category": category,
                "type": type
            }

            stage_results.append(plugin_dict)
        return stage_status, stage_results


    def run_step(
            self, step_name, stages, step_context, step_options, step_data,
            stages_order, step_type
    ):
        #TODO: Check if the step_context description is correct,
        # is it a list or a dictionary?
        '''
        Returns the bool status and the result list dictionary of executing all
        the stages in the step.
        This function executes all the defined stages for for this step using
        the :meth:`run_stage` with the given *stage_order*.

        *step_name* : Name of the step that's executing.

        *stages* : List of stages that has to execute.

        *step_context* : Context list with the dictionary with the context
        where it has to be executed.

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

                # if not stage_status:
                #     raise Exception(
                #         'An error occurred during the execution of the '
                #         'stage name {}'.format(stage_name))

                stage_dict = {
                    "name": stage_name,
                    "result": stage_result,
                    "status": stage_status,
                    "category": category,
                    "type": type
                }

                step_results.append(stage_dict)
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
        # TODO: I'll have to remove the plugin_type key from the plugins in the
        #  definitions and everywhere else that is used. The new name will be type,
        #  and the current type=plugin will be category.


        #TODO: To reduce the amount of code, in a second stage we can try to get
        # all the type steps and execute all them un a loop just checking then
        # if they are in context components or finalizers....

        contexts_steps = data[constants.CONTEXTS]
        contexts_results = []
        contexts_status = True
        for context_step in contexts_steps:
            step_name = context_step['name']
            step_stages = context_step['stages']
            step_enabled = context_step['enabled']
            step_stage_order = context_step['stage_order']
            step_category = context_step['category']
            step_type = context_step['type']

            if not step_enabled:
                self.logger.info(
                    'Skipping step {} as it been disabled'.format(
                        step_name
                    )
                )
                continue

            # Avoid passing contexts_results to avoid modifying the data on it
            #  during the step/stage and plugin execution
            step_data = copy.deepcopy(contexts_results)

            step_status, step_result = self.run_step(
                step_name=step_name,
                stages=step_stages,
                step_context=None,
                step_options=[],
                step_data=step_data,
                stages_order=step_stage_order,
                step_type=step_type
            )

            if not step_status:
                contexts_status = False
                # raise Exception('An error occurred during the execution of the '
                #                             'step name {}'.format(step_name))


            step_dict = {
                "name": step_name,
                "result": step_result,
                "status": step_status,
                "category": step_category,
                "type": step_type
            }

            contexts_results.append(step_dict)

        if not contexts_status:
            raise Exception('An error occurred during the execution of the '
                            'context')

        # We get the context dictionary from the latest executed plugin of the
        # latest context stage of the latest context step. In case in the future
        # we want to use multiple context we will have to create the
        # corresponding loops of context and components...
        context_latest_step = contexts_results[-1]
        context_latest_stage = context_latest_step.get('result')[-1]
        context_latest_plugin = context_latest_stage.get('result')[-1]
        context_latest_plugin_result = context_latest_plugin.get('result')
        context_data = context_latest_plugin_result


        components_steps = data[constants.COMPONENTS]
        components_result = []
        components_status = True

        for component_step in components_steps:
            step_name = component_step['name']
            step_stages = component_step['stages']
            step_enabled = component_step['enabled']
            step_stage_order = component_step['stage_order']
            step_category = component_step['category']
            step_type = component_step['type']

            #TODO: we could avoid this if we modify the PublisherFinalizerPlugin
            # line 224 and the finalizers plugin itself to not pass the name of
            # the component as it's not needed now.
            step_options = {'component_name': step_name}
            step_data = copy.deepcopy(components_result)

            if not step_enabled:
                self.logger.info(
                    'Skipping step {} as it been disabled'.format(
                        step_name
                    )
                )
                continue
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
                components_status = False
                # raise Exception('An error occurred during the execution of the '
                #                             'step name {}'.format(step_name))

            step_dict = {
                "name": step_name,
                "result": step_result,
                "status": step_status,
                "category": step_category,
                "type": step_type
            }

            components_result.append(step_dict)

        #TODO: check if we want this exceptions here or we already stoped on the
        # mandatory ones
        if not components_status:
            raise Exception(
                'An error occurred during the execution of the components'
            )

        #TODO: check if we really need to have the result of the outputs
        # with the component name and check why is not cleaning up correcly all that is not output

        components_output = copy.deepcopy(components_result)
        i = 0
        for component_step in components_result:
            for component_stage in component_step.get("result"):
                self.logger.debug(
                    "Checking stage name {} of type {}".format(
                        component_stage.get("name"), component_stage.get("type")
                    )
                )
                if component_stage.get("type") != constants.OUTPUT:
                    self.logger.debug(
                        "Removing stage name {} of type {}".format(
                            component_stage.get("name"), component_stage.get("type")
                        )
                    )
                    components_output[i]['result'].remove(component_stage)
            i += 1

        finalizers_steps = data[constants.FINALIZERS]
        # Add the components outputs as result of the finalizer to passe them
        # as data on each step
        finalizers_result = copy.deepcopy(components_output)
        finalizers_status = True

        for finalizer_step in finalizers_steps:
            step_name = finalizer_step['name']
            step_stages = finalizer_step['stages']
            step_enabled = finalizer_step['enabled']
            step_stage_order = finalizer_step['stage_order']
            step_category = finalizer_step['category']
            step_type = finalizer_step['type']

            if not step_enabled:
                self.logger.info(
                    'Skipping step {} as it been disabled'.format(
                        step_name
                    )
                )
                continue

            step_data = copy.deepcopy(finalizers_result)

            step_status, step_result = self.run_step(
                step_name=step_name,
                stages=step_stages,
                step_context=context_data,
                step_options=[],
                step_data=step_data,
                stages_order=step_stage_order,
                step_type=step_type
            )

            if not step_status:
                finalizers_status = False

            step_dict = {
                "name": step_name,
                "result": step_result,
                "status": step_status,
                "category": step_category,
                "type": step_type
            }

            finalizers_result.append(step_dict)

        # TODO: check if we want this exceptions here or we already stoped on the
        #  mandatory ones
        if not finalizers_status:
            raise Exception(
                'An error occurred during the execution of the components'
            )

        #TODO: maybe we could be returning the finalizers_result? or maybe not
        # needed and just dd it to a log or pas it to the notify client
        return True

