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

    def _update_registry(
            self, step_name, stage_name, plugin_name, plugin_result
    ):
        self._registry[step_name][stage_name][plugin_name] = plugin_result

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

    # Base functions for loader, opener and publisher

    def run_stage(
        self,
        stage_definition,
        step_name
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

        plugins = stage_definition.get_all(category='plugins')
        status = True
        for plugin_definition in plugins:
            if not plugin_definition.enabled:
                self.logger.debug(
                    'Skipping step {} as it has been disabled'.format(
                        plugin_definition.name
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
                    status=constants.status.RUNNING_STATUS,
                    results=None,
                )

            # Pass all previous stage executed plugins result
            plugin_data = copy.deepcopy(
                self._registry[step_name]
            )
            # If finalizer add all component results.
            if step_name == 'finalizer':
                plugin_data['component'] =  copy.deepcopy(
                    self._registry['component']
                )

            plugin_info = self.run_plugin(
                plugin_name=plugin_definition.plugin,
                plugin_default_method=plugin_definition.default_method,
                # We don't want to pass the information of the previous plugin,
                # so that is why we only pass the data of the previous stage.
                # TODO: Instead of using stage data implement the self stage_registry or something like that, same for context data
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

            self._update_registry(
                step_name,
                stage_definition.name,
                plugin_name=plugin_info['plugin_name'],
                plugin_result=plugin_info['plugin_method_result']
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
                        step_name
                    )
                )
                break

        # Return status of the stage execution
        return status


    def run_step(self, step_definition):
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

        status = True
        stages = step_definition.get_all(category='plugins')
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
            status = self.run_stage(stage_definition, step_definition.name)
            if not status:
                break
        self.event_manager.publish.notify_definition_progress_client(
            host_id=self.host_id,
            step_type=step_type,
            step_name=step_name,
            stage_name=stage_name,
            total_plugins=None,
            current_plugin_index=None,
            status=constants.status.ERROR_STATUS,
            results=step_results,
        )

        # Return status of the stage execution
        return status

    # TODO: clean up this code and use definition object to simplify.
    def run_definition(self, definition):
        '''
        Runs the whole definition from the provided *data*.
        Call the method :meth:`run_step` for each context, component and
        finalizer steps.

        *data* : pipeline['data'] provided from the client host connection at
        :meth:`~ftrack_framework_core.client.HostConnection.run` Should be a
        valid definition.
        '''

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
        if not status:
            pass



        # TODO:
        #  Context step:
        #      context_data = None,
        #      data = previous context step
        #          plugins results
        #  Components step:
        #      context_data = result of all context step
        #          (So dictionary with all context plugins)
        #      data = Previous component step results
        #  Finalizer step:
        #      context_data = result of all context step
        #          (So dictionary with all context plugins)
        #      data = Importer, exporter and post_import results of the
        #          component step + Previous finalizer step results

