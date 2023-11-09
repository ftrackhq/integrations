# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import copy

import ftrack_constants.framework as constants
from ftrack_framework_engine import BaseEngine


class LoadPublishEngine(BaseEngine):
    '''
    Base engine class.
    '''

    name = 'load_publish'
    engine_types = [
        constants.tools.types.LOADER,
        constants.tools.types.OPENER,
        constants.tools.types.PUBLISHER,
    ]
    '''Supported engine types for this engine class'''

    @property
    def context_data(self):
        '''List of all the context plugins results.'''
        if not self._context_data:
            return None
        return self._context_data

    def __init__(
        self,
        event_manager,
        ftrack_object_manager,
        host_types,
        host_id,
        asset_type_name=None,
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
            event_manager,
            ftrack_object_manager,
            host_types,
            host_id,
            asset_type_name,
        )
        self._context_data = []
        self._registry = {}

    def reset_registry(self):
        '''Sets the context_data and registry variables to 0'''
        self._context_data = []
        self._registry = {}

    def _update_registry(
        self, step_type, step_name, stage_name, plugin_name, plugin_result
    ):
        '''
        Function to update the self._registry variable with the result of
        all the ran plugins.
        '''

        if not self._registry.get(step_type):
            self._registry[step_type] = {}
        if not self._registry[step_type].get(step_name):
            self._registry[step_type][step_name] = {}
        if not self._registry[step_type][step_name].get(stage_name):
            self._registry[step_type][step_name][stage_name] = {}
        # TODO: if the plugin is defined twice in the same stage, the result
        #  will be overriden. To avoid this, we could make the plugin name unic
        #  or add the description if the plugin to the dictionary (But I would
        #  try to avoid that to not make it more complex. So I'll go for the
        #  first option)
        self._registry[step_type][step_name][stage_name][
            plugin_name
        ] = plugin_result

    def run_plugin(
        self,
        plugin_name,
        plugin_default_method=None,
        plugin_options=None,
        plugin_data=None,
        plugin_context_data=None,
        plugin_method=None,
        plugin_widget_id=None,
        plugin_widget_name=None,
        plugin_step_name=None,
        plugin_stage_name=None,
    ):
        '''Call the run_plugin method from the base engine'''
        return super(LoadPublishEngine, self).run_plugin(
            plugin_name=plugin_name,
            plugin_default_method=plugin_default_method,
            plugin_options=plugin_options,
            plugin_data=plugin_data,
            plugin_context_data=plugin_context_data,
            plugin_method=plugin_method,
            plugin_widget_id=plugin_widget_id,
            plugin_widget_name=plugin_widget_name,
            plugin_step_name=plugin_step_name,
            plugin_stage_name=plugin_stage_name,
        )

    def run_stage(self, stage_config, step_type, step_name):
        '''
        Returns the bool status of running all the plugins in the given
        *stage_config*.

        *stage_config* : :obj:`~ftrack_framework_core.tool_config.Stage`

        *step_type* : Type of the parent step
        *step_name* : Name of the parent step
        '''

        plugins = stage_config.get_all(category='plugin')
        status = True
        i = 0
        for plugin_config in plugins:
            if not plugin_config.enabled:
                self.logger.debug(
                    'Skipping step {} as it has been disabled'.format(
                        plugin_config.plugin_name
                    )
                )
                continue

            self.event_manager.publish.notify_tool_config_progress_client(
                host_id=self.host_id,
                step_type=step_type,
                step_name=step_name,
                stage_name=stage_config.stage_name,
                plugin_name=plugin_config.plugin_name,
                total_plugins=len(plugins),
                current_plugin_index=i,
                status=constants.status.RUNNING_STATUS,
            )

            plugin_data = {}
            # If finalizer add all registry.
            if step_type == 'finalizer':
                plugin_data = copy.deepcopy(self._registry)
            else:
                # Pass all previous stage executed plugins result
                plugin_data = copy.deepcopy(self._registry.get(step_type))

            plugin_info = self.run_plugin(
                plugin_name=plugin_config.plugin_name,
                plugin_default_method=plugin_config.default_method,
                # We don't want to pass the information of the previous plugin,
                # so that is why we only pass the data of the previous stage.
                plugin_data=plugin_data,
                # From the tool_config + stage_options
                plugin_options=plugin_config.options,
                # Data from the plugin context
                plugin_context_data=self.context_data,
                # default_method is defined in the tool_configs
                plugin_method=plugin_config.default_method,
                plugin_widget_id=plugin_config.widget_id,
                plugin_widget_name=plugin_config.widget_name,
                plugin_step_name=step_name,
                plugin_stage_name=stage_config.stage_name,
            )

            if step_type == 'context':
                self._context_data.append(plugin_info['plugin_method_result'])
            else:
                self._update_registry(
                    step_type,
                    step_name,
                    stage_config.stage_name,
                    plugin_name=plugin_info['plugin_name'],
                    plugin_result=plugin_info['plugin_method_result'],
                )
            self.event_manager.publish.notify_tool_config_progress_client(
                host_id=self.host_id,
                step_type=step_type,
                step_name=step_name,
                stage_name=stage_config.stage_name,
                plugin_name=plugin_config.plugin_name,
                total_plugins=len(plugins),
                current_plugin_index=i,
                status=plugin_info['plugin_status'],
            )
            status = constants.status.status_bool_mapping[
                plugin_info['plugin_status']
            ]
            if not status:
                # We log an error if a plugin on the stage failed.
                self.logger.error(
                    "Execution of the plugin {} in stage {} of step {} "
                    "failed. Stopping run tool_config".format(
                        plugin_config.plugin_name,
                        stage_config.stage_name,
                        step_name,
                    )
                )
                break
            i += 1

        # Return status of the stage execution
        return status

    def run_step(self, step_config):
        '''
        Returns the bool status of running all the stages in the given
        *step_config*.
        *step_config* : :obj:`~ftrack_framework_core.tool_config.Step`
        '''

        status = True
        stages = step_config.get_all(category='stage')
        for stage_config in stages:
            # We don't need the stage order because the stage order is given by
            # order in the tool_config and that is a list so its already sorted.
            if not stage_config.enabled:
                self.logger.debug(
                    'Skipping step {} as it has been disabled'.format(
                        stage_config.stage_name
                    )
                )
                continue
            status = self.run_stage(
                stage_config,
                step_config.step_type,
                step_config.step_name,
            )
            if not status:
                break

        # Return status of the stage execution
        return status

    def run_tool_config(self, tool_config):
        '''
        Runs all the steps in the given *tool_config*.
        *tool_config* : :obj:`~ftrack_framework_core.tool_config.Tool_configObject`

        # Data Workflow:
        #  Context step:
        #      context_data = None,
        #      data = previous context step
        #          plugins results
        #      Return: Set the context_data property. (It will be a list of all
        #              the results)
        #  Components step:
        #      context_data = result of all context step (self.context_data)
        #          (List with the result of all the context plugins)
        #      data = Previous component step results
        #  Finalizer step:
        #      context_data = result of all context step (self.context_data)
        #          (List with the result of all the context plugins)
        #      data = The entire registry: Previous component step results +
        #             previous finalizer step results.

        '''

        self.reset_registry()

        status = True
        steps = tool_config.get_all(category='step')

        # Check that tool_config contains at least the required step types
        step_types = []
        required_step_types = ['context', 'finalizer', 'component']
        for step in steps:
            step_types.append(step.step_type)
        if not set(required_step_types).issubset(step_types):
            raise Exception(
                "Given tool_config is not supported by this engine. "
                "Required steps {} are not in the steps of this "
                "tool_config: {}".format(required_step_types, step_types)
            )
        for step_config in steps:
            if not step_config.enabled:
                self.logger.debug(
                    'Skipping step {} as it has been disabled'.format(
                        step_config.step_name
                    )
                )
                continue

            status = self.run_step(step_config)
            if not status:
                break
        return status
