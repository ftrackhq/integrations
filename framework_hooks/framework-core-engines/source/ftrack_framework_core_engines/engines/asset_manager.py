# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import copy

import ftrack_constants.framework as constants
from ftrack_constants.framework import asset as asset_const
from ftrack_framework_engine import BaseEngine
from ftrack_framework_core.asset.asset_info import FtrackAssetInfo


class AssetManagerEngine(BaseEngine):
    '''
    Asset manager engine class. This engine is used to manage DCC assets through
    base run plugin method.
    '''

    name = 'asset_manager'
    engine_types = [
        constants.definition.ASSET_MANAGER,
    ]
    '''Engine types for this engine class'''

    @property
    def context_data(self):
        '''
        Returns the context_data for the current asset processed.
        '''
        return self._context_data

    @context_data.setter
    def context_data(self, value):
        '''
        Set the context_data for the current asset processed, and clears the registry.
        '''
        self._context_data = value
        self.__registry = {}

    @property
    def asset_info(self):
        '''
        Returns the asset info for the current asset processed.
        '''
        return self.context_data['asset_info']

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
        super(AssetManagerEngine, self).__init__(
            event_manager,
            ftrack_object_manager,
            host_types,
            host_id,
            asset_type_name,
        )
        self._context_data = None
        self.__registry = {}

    def _update_registry(
        self, step_type, step_name, stage_name, plugin_name, plugin_result
    ):
        '''
        Function to update the self.__registry variable with the result of
        all the runned plugins.
        '''

        if not self.__registry.get(step_type):
            self.__registry[step_type] = {}
        if not self.__registry[step_type].get(step_name):
            self.__registry[step_type][step_name] = {}
        if not self.__registry[step_type][step_name].get(stage_name):
            self.__registry[step_type][step_name][stage_name] = {}
        self.__registry[step_type][step_name][stage_name][
            plugin_name
        ] = plugin_result

    def run_stage(self, stage_definition, step_type, step_name):
        '''
        Returns the bool status of running all the plugins in the given
        *stage_definition*.

        *stage_definition* : :obj:`~ftrack_framework_core.definition.Stage`

        *step_type* : Type of the parent step
        *step_name* : Name of the parent step
        '''
        plugins = stage_definition.get_all(category='plugin')
        status = constants.status.SUCCESS_STATUS
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

            # Pass all previous stage executed plugins result
            plugin_data = copy.deepcopy(self.__registry.get(step_type))

            plugin_info = self.run_plugin(
                plugin_name=plugin_definition.plugin,
                plugin_default_method=plugin_definition.default_method,
                # We don't want to pass the information of the previous plugin,
                # so that is why we only pass the data of the previous stage.
                plugin_data=plugin_data,
                # From the definition + stage_options
                plugin_options=plugin_definition.options.to_dict(),
                # Data from the plugin context
                plugin_context_data=self.context_data,
                # default_method is defined in the definitions
                plugin_method=plugin_definition.default_method,
                plugin_widget_id=plugin_definition.widget_id,
                plugin_widget_name=plugin_definition.widget,
            )

            plugin_result = plugin_info['plugin_method_result']

            self._update_registry(
                step_type,
                step_name,
                stage_definition.name,
                plugin_name=plugin_info['plugin_name'],
                plugin_result=plugin_result,
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
            bool_status = constants.status.status_bool_mapping[
                plugin_info['plugin_status']
            ]
            if not bool_status:
                # We log an error if a plugin on the stage failed.
                self.logger.error(
                    "Execution of the plugin {} in stage {} of step {} "
                    "failed. Stopping run definition".format(
                        plugin_definition.plugin,
                        stage_definition.name,
                        step_name,
                    )
                )
                return constants.status.ERROR_STATUS
            if step_type in ['update', 'change_version']:
                if stage_definition.type == 'query':
                    # Check if the plugin returned a new version
                    if len(plugin_result or []) != 1:
                        self.logger.error(
                            'Query plugin should return one version'
                        )
                        return constants.status.ERROR_STATUS
                    assert_version_entity = self.session.query(
                        'AssetVersion where id is {}'.format(
                            plugin_result[0]['id']
                        )
                    ).one()
                    if (
                        assert_version_entity['version']
                        <= self.asset_info[asset_const.VERSION_NUMBER]
                    ):
                        self.logger.error(
                            'Query plugin did not return a version higher than the current'
                        )
                        # Signal to the caller that the plugin did not return a newer version - skip asset
                        return constants.status.DEFAULT_STATUS
                elif stage_definition.type == 'remove':
                    # TODO: Asset removed, prepare load - the asset info with new version
                    # Implement this in DCC where we have proper loaded asset info to work with
                    pass

            i += 1

        # Return status of the stage execution
        return status

    def run_step(self, step_definition):
        '''
        Returns the bool status of running all the stages in the given
        *step_definition*.
        *step_definition* : :obj:`~ftrack_framework_core.definition.Step`
        '''

        status = constants.status.SUCCESS_STATUS
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
            if status != constants.status.SUCCESS_STATUS:
                break

        # Return status of the stage execution
        return status

    def run_definition(self, definition, context_data=None):
        '''
        (Override) Runs the action step type outlined in *data*, within the given *definition*
        on the list of assets provided in *data*.
        *definition* : :obj:`~ftrack_framework_core.definition.DefinitionObject`

        '''

        assert (
            context_data
            and 'action' in context_data
            and 'assets' in context_data
        ), "Cannot run definition without context data, providing action (type) and assets is required."

        status = True
        action_type = context_data['action']
        assets = context_data['assets']

        # First, locate the step configuration for the given action

        step_configuration = None

        steps = definition.get_all(category='step')
        for step in steps:
            if not step.enabled:
                self.logger.debug(
                    'Skipping step {} as it has been disabled'.format(
                        step.name
                    )
                )
                continue
            elif step.type not in action_type:
                self.logger.debug(
                    'Skipping step {} as it is not part of the action ()'.format(
                        step.name, action_type
                    )
                )
                continue
            step_configuration = step
            break

        if not step_configuration:
            self.logger.error(
                'No step configuration found for action {}'.format(action_type)
            )
            return False

        for asset_info_raw in assets:
            # Augment context data with the single asset instead of the list
            self.context_data = {}
            for key, value in list(context_data.items()):
                if key == 'assets':
                    self.context_data['asset_info'] = FtrackAssetInfo(
                        asset_info_raw
                    )
                else:
                    self.context_data[key] = value

            self.logger.debug(
                'Running definition action step "{}" on asset: '.format(
                    action_type, self.context_data['asset_info']
                )
            )

            status = self.run_step(step_configuration)

            if status == constants.status.ERROR_STATUS:
                break

        return status
