# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

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

    def run_stage(
            self, stage_name, plugins, stage_context, stage_options, stage_data,
            plugins_order=None,
            step_type=None
    ):
        plugin_type = '{}.{}'.format(self.engine_type, stage_name)

        stage_status = True
        stage_results = []

        for plugin in plugins:
            result = None
            plugin_name = plugin['plugin']
            plugin_options = plugin['options']
            # So the idea is to have the
            # plugin_options['component_name'] = step_name coming from the
            # stage options
            plugin_options.update(stage_options)
            #TODO: somehow we have to activate this for components
            #if step_type == constants.COMPONENTS:
            #     plugin_options['component_name'] = step_name
            plugin_status, plugin_result = self._run_plugin(
                plugin, plugin_type,
                data=data,#collected_data,
                options=plugin_options,
                context=stage_context,
                method="run"
            )

            if plugin_result:
                # TODO: we could add the run_method key to the definitions and
                # get this default or run methon from there
                result = plugin_result.get("run")
            # TODO: this should be aded if its a context
            # we should be saing if step_type == contexts or parent == contexts
            if step_type == constants.CONTEXTS:
                result['asset_type'] = self.asset_type
            bool_status = constants.status_bool_mapping[plugin_status]
            if not bool_status:
                stage_status = False

            plugin_dict = {
                "name": plugin_name,
                "result": result,
                "status": bool_status
            }

            stage_results.append(plugin_dict)
        return stage_status, stage_results


    def run_step(self, step_name, stages, step_context, step_options, step_data, stages_order, step_type):
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

        step_status = True
        step_results = []

        for stage in stages:
            for stage_name in stages_order:
                if stage_name != stage['name']:
                    continue

                stage_plugins = stage['plugins']

                if not stage_plugins:
                    continue

                stage_status, stage_result = self.run_stage(
                    stage_name=stage_name,
                    plugins=stage_plugins,
                    stage_context=step_context,
                    stage_options=step_options,
                    stage_data=step_data,
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
                    "status": stage_status
                }

                step_results.append(stage_dict)
        return step_status, step_results
        # TODO: be carfully we should add the result to a key with the
        # name of the stage
        # {
        #     "name": stage_name,
        #     stage_name: [
        #         {
        #             "name": "plugin1",
        #             "plugin1": (["the result"], "the message"),
        #             "status": "true"
        #         },
        #         {
        #             "name": "plugin2",
        #             "plugin1": (["the result"], "the message"),
        #             "status": "false"
        #         }
        #     ],#stage_result #This should be a list
        #     status: "false"
        # }

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

    def run_definition(self, data):
        '''
        Runs the whole definition from the provided *data*.
        Call the methods :meth:`run_context` , :meth:`run_components` and
        :meth:`run_finalizer`. Raises Exceptions if any of this methods fails.

        *data* : pipeline['data'] provided from the client host connection at
        :meth:`~ftrack_connect_pipeline.client.HostConnection.run` Should be a
        valid definition.
        '''

        contexts_steps = data[constants.CONTEXTS]
        contexts_results = []
        contexts_status = True
        for context_step in contexts_steps:
            step_name = context_step['name']
            step_stages = context_step['stages']
            step_enabled = context_step['enabled']
            step_stage_order = context_step['stage_order']
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
                step_context=None,
                step_options=None,
                step_data=None,
                stages_order=step_stage_order,
                step_type = constants.CONTEXTS
            )

            if not step_status:
                contexts_status = False
                # raise Exception('An error occurred during the execution of the '
                #                             'step name {}'.format(step_name))


            step_dict = {
                "name": step_name,
                "result": step_result,
                "status": step_status
            }

            contexts_results.append(step_dict)

        if not contexts_status:
            raise Exception('An error occurred during the execution of the '
                            'context')

        # We get the context dictionary from the lates executed plugin of the
        # latest context stage of the lates context step. In case in the future
        # we want to use multiple context we will have to create the
        # corresponding loops of context and components...
        context_latest_step = contexts_results[-1]
        context_latest_stage = context_latest_step.get('result')[-1]
        context_latest_plugin = context_latest_stage.get('result')[-1]
        context_latest_plugin_result = context_latest_plugin.get('result')[-1]
        context_data = context_latest_plugin_result


        components_steps = data[constants.COMPONENTS]
        components_result = []
        components_status = True

        for component_step in components_steps:
            step_name = component_step['name']
            step_stages = component_step['stages']
            step_enabled = component_step['enabled']
            step_stage_order = component_step['stage_order']
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
                context_data=context_data,
                stages_order=step_stage_order
            )

            if not step_status:
                components_status = False
                # raise Exception('An error occurred during the execution of the '
                #                             'step name {}'.format(step_name))

            step_dict = {
                "name": step_name,
                "result": step_result,
                "status": step_status
            }

            components_result.append(step_dict)

        #TODO: check if we want this exceptions here or we already stoped on the
        # mandatory ones
        if not components_status:
            raise Exception(
                'An error occurred during the execution of the components'
            )
        # Components result should look like this:
        # components_result = [
        #     {
        #         "name":"comp1",
        #         "result":[
        #             {
        #                 "name":"collector",
        #                 "result":[
        #                     {
        #                         "name":"plug1_coolect",
        #                         "result":[{}]
        #                     }
        #                 ]
        #             },
        #             {
        #                 "name":"output",
        #                 "result":[
        #                     {
        #                         "name":"plug1",
        #                         "result":[{}]
        #                     }
        #                 ]
        #             }
        #         ]
        #     },
        #     {
        #         "name":"comp2",
        #         "result":[
        #             {
        #                 "name":"collector",
        #                 "result":[
        #                     {
        #                         "name":"plug2_coolect",
        #                         "result":[{}]
        #                     }
        #                 ]
        #             },
        #             {
        #                 "name":"output",
        #                 "result":[
        #                     {
        #                         "name":"plug2",
        #                         "result":[{}]
        #                     }
        #                 ]
        #             }
        #         ]
        #     }
        # ]


        # Filter the components_result list to only containt the outputs result
        components_output = components_result.copy()
        for component_step in components_output:
            i = 0
            for component_stage in component_step.get("result"):
                if (
                        component_stage.get("name") != constants.OUTPUT or
                        component_stage.get("name") != constants.POST_IMPORT
                ):
                    component_step['result'].pop(i)
                i += 1

        finalizers_steps = data[constants.COMPONENTS]
        finalizers_result = []
        finalizers_status = True

        for finalizer_step in finalizers_steps:
            step_name = finalizer_step['name']
            step_stages = finalizer_step['stages']
            step_enabled = finalizer_step['enabled']
            step_stage_order = finalizer_step['stage_order']
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
                context_data=context_data,
                stages_order=step_stage_order
            )

            if not step_status:
                finalizers_status = False

            step_dict = {
                "name": step_name,
                "result": step_result,
                "status": step_status
            }

            finalizers_result.append(step_dict)

        # TODO: check if we want this exceptions here or we already stoped on the
        # mandatory ones
        if not finalizers_status:
            raise Exception(
                'An error occurred during the execution of the components'
            )

        #TODO: Now we should be pasing the data from context to components to finalizers...




        # context_status, context_result = self.run_context(context_plugins)
        # if not all(context_status):
        #     raise Exception('An error occurred during the execution of the '
        #                     'context')
        # context_result['asset_type'] = self.asset_type
        #
        # components = data[constants.COMPONENTS]
        # components_result = []
        # components_status = []
        #
        # for component in components:
        #     component_name = component['name']
        #     component_stages = component['stages']
        #     component_enabled = component['enabled']
        #     if not component_enabled:
        #         self.logger.info(
        #             'Skipping component {} as it been disabled'.format(
        #                 component_name
        #             )
        #         )
        #         continue
        #
        #     component_status, component_result = self.run_component(
        #         component_name, component_stages, context_result,
        #         data['_config']['stage_order']
        #     )
        #
        #     if not all(component_status.values()):
        #         raise Exception('An error occurred during the execution of the '
        #                         'component name {}'.format(component_name))
        #
        #     components_status.append(component_status)
        #     components_result.append(component_result)

        finalizer_plugins = data[constants.FINALIZERS]
        finalizer_data = {}
        for item in components_result:
            last_component = constants.OUTPUT
            if constants.POST_IMPORT in list(item.keys()):
                last_component = constants.POST_IMPORT
            for output in item.get(last_component):
                if not output:
                    continue

                for key, value in output.items():
                    finalizer_data[key] = value

        finalizers_status, finalizers_result = self.run_finalizer(
            finalizer_plugins, finalizer_data, context_result
        )
        if not all(finalizers_status):
            raise Exception('An error occurred during the execution of the '
                            'finalizers')

        return True


