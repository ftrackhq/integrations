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
        constants.definition.LOADER,
        constants.definition.OPENER,
        constants.definition.PUBLISHER,
    ]
    '''Engine type for this engine class'''

    @property
    def context_data(self):
        '''List of all the context plugins results.'''
        if not self._context_data:
            return None
        return self._context_data

    # TODO: double check if we really need to declare the init here.
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
        all the runned plugins.
        '''

        if not self._registry.get(step_type):
            self._registry[step_type] = {}
        if not self._registry[step_type].get(step_name):
            self._registry[step_type][step_name] = {}
        if not self._registry[step_type][step_name].get(stage_name):
            self._registry[step_type][step_name][stage_name] = {}
        # TODO: if the plugin is defined twice in the same stage, the result
        #  will be overrided. To avoid this, we could make the plugin name unic
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
        )

    def run_stage(self, stage_definition, step_type, step_name):
        '''
        Returns the bool status of running all the plugins in the given
        *stage_definition*.

        *stage_definition* : :obj:`~ftrack_framework_core.definition.Stage`

        *step_type* : Type of the parent step
        *step_name* : Name of the parent step
        '''

        plugins = stage_definition.get_all(category='plugin')
        status = True
        i = 0
        for plugin_definition in plugins:
            if not plugin_definition.enabled:
                self.logger.debug(
                    'Skipping step {} as it has been disabled'.format(
                        plugin_definition.name
                    )
                )
                continue

            self.event_manager.publish.notify_definition_progress_client(
                host_id=self.host_id,
                step_type=step_type,
                step_name=step_name,
                stage_name=stage_definition.name,
                plugin_name=plugin_definition.name,
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
                plugin_name=plugin_definition.plugin,
                plugin_default_method=plugin_definition.default_method,
                # We don't want to pass the information of the previous plugin,
                # so that is why we only pass the data of the previous stage.
                plugin_data=plugin_data,
                # From the definition + stage_options
                plugin_options=plugin_definition.options,
                # Data from the plugin context
                plugin_context_data=self.context_data,
                # default_method is defined in the definitions
                plugin_method=plugin_definition.default_method,
                plugin_widget_id=plugin_definition.widget_id,
                plugin_widget_name=plugin_definition.widget,
            )

            if step_type == 'context':
                self._context_data.append(plugin_info['plugin_method_result'])
            else:
                self._update_registry(
                    step_type,
                    step_name,
                    stage_definition.name,
                    plugin_name=plugin_info['plugin_name'],
                    plugin_result=plugin_info['plugin_method_result'],
                )
            self.event_manager.publish.notify_definition_progress_client(
                host_id=self.host_id,
                step_type=step_type,
                step_name=step_name,
                stage_name=stage_definition.name,
                plugin_name=plugin_definition.name,
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
                    "failed. Stopping run definition".format(
                        plugin_definition.plugin,
                        stage_definition.name,
                        step_name,
                    )
                )
                break
            i += 1

        # Return status of the stage execution
        return status

    def run_step(self, step_definition):
        '''
        Returns the bool status of running all the stages in the given
        *step_definition*.
        *step_definition* : :obj:`~ftrack_framework_core.definition.Step`
        '''

        status = True
        stages = step_definition.get_all(category='stage')
        for stage_definition in stages:
            # We don't need the stage order because the stage order is given by
            # order in the definition and that is a list so its already sorted.
            if not stage_definition.enabled:
                self.logger.debug(
                    'Skipping step {} as it has been disabled'.format(
                        stage_definition.name
                    )
                )
                continue
            status = self.run_stage(
                stage_definition, step_definition.type, step_definition.name
            )
            if not status:
                break

        # Return status of the stage execution
        return status

    def run_definition(self, definition, context_data=None):
        '''
        (Override) Runs all the steps in the given *definition*, giving optional
        starter *context_data*.
        *definition* : :obj:`~ftrack_framework_core.definition.DefinitionObject`

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
        steps = definition.get_all(category='step')
        for step_definition in steps:
            if not step_definition.enabled:
                self.logger.debug(
                    'Skipping step {} as it has been disabled'.format(
                        step_definition.name
                    )
                )
                continue

            status = self.run_step(step_definition)
            if not status:
                break
        return status
