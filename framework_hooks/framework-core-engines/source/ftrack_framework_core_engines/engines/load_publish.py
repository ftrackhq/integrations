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

        plugins = stage.get_all(category='plugins')
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

            plugin_data = copy.deepcopy(stage_data)
            # TODO: maybe create a step registry to registry the result and the status of each executed step.
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
            bool_status = constants.status.status_bool_mapping[
                plugin_info['plugin_status']
            ]
            if not bool_status:
                # TODO: carefull, this is a lstatus for the entire stage execution.
                self.update_stage(stage_name, "status", False)
                stage_status = False
                result = plugin_info['plugin_method_result']
                # We log a warning if a plugin on the stage failed.
                self.logger.error(
                    "Execution of the plugin {} failed.".format(
                        plugin_definition.plugin
                    )
                )
            # TODO: carefull, this is a list of results for each plugin, so we are appending to that list
            self.update_stage(stage_name, "results", plugin_info)
            # stage_info = {
            #                 "name": stage_name,
            #                 "result": stage_result,
            #                 "status": stage_status,
            #                 "category": category,
            #                 "type": type,
            #             }


        # Return status of the stage execution
        return self.stage_registry['status']


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
            stage_data = copy.deepcopy(previous_stage_results)
            # TODO: maybe create a step registry to registry the result and the status of each executed step.
            status = self.run_stage(stage_definition, stage_data)
            if not status:
                # TODO: carefull, this is a lstatus for the entire stage execution.
                self.update_step(
                    step_definition.name,
                    "status",
                    constants.status.ERROR_STATUS
                )
                self.logger.error(
                    "Execution of the stage {} failed.".format(stage_definition.name)
                )
                break

            # TODO: carefull, this is a list of results for each plugin, so we are appending to that list
            self.update_step(step_definition.name, "results", self.stage_registry.results)
            # stage_info = {
            #                 "name": stage_name,
            #                 "result": stage_result,
            #                 "status": stage_status,
            #                 "category": category,
            #                 "type": type,
            #             }

        bool_status = constants.status.status_bool_mapping[
            self.step_registry['status']
        ]
        if bool_status:
            self.update_step(
                step_definition.name,
                "status",
                constants.status.SUCCESS_STATUS)

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
        return self.step_registry['status']

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

        steps = definition.get_all(category='step')
        for step_definition in steps:
            if not step_definition.enabled:
                self.logger.debug(
                    'Skipping step {} as it has been disabled'.format(
                        step_definition.name
                    )
                )
                continue
            step_data = None
            if step_definition.name == 'finalizer':
                step_data = self.step_registry['component'].result

            # TODO: maybe create a step registry to registry the result and the status of each executed step.
            status, result = self.run_step(step_definition, step_data)
            if step_definition.name == 'context':
                self._context_data = self.step_registry[step_definition.name].result
                step_data = None



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

