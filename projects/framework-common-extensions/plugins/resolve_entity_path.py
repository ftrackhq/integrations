# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import sys

from ftrack_utils.string import str_version
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError
import clique


class ResolveEntityPathsPlugin(BasePlugin):
    name = 'resolve_entity_path'

    def _resolve_entity_paths(self, options):
        '''Evaluate list of entities passed on in 'options', ensure
        a single component and resolve path. Return as dictionary'''
        result = {}
        entities = options.get('selection', [])
        if not entities:
            raise PluginExecutionError('No entities selected')
        if len(entities) != 1:
            raise PluginExecutionError('Only one single entity supported')
        entity = entities[0]
        if entity['entityType'].lower() != 'component':
            raise PluginExecutionError('Only Component entity supported')

        component_id = entity['entityId']
        component = self.session.query(
            f'Component where id={component_id}'
        ).first()
        if not component:
            raise PluginExecutionError(f'Component not found: {component_id}')

        result['entity_id'] = component_id
        result['entity_type'] = entity['entityType']

        # Check path
        location = self.session.pick_location()
        try:
            component_path = location.get_filesystem_path(component)
        except Exception as error:
            error_message = (
                f'Could not get the path for component {component_id}: {error}'
            )
            self.logger.exception(error_message)
            raise PluginExecutionError(error_message)

        if isinstance(component, self.session.types['SequenceComponent']):
            result['is_sequence'] = True
            file_names = [
                location.get_filesystem_path(member)
                for member in component['members']
            ]  # Adjust as necessary
            collection, remainder = clique.assemble(file_names)
            result['component_path'] = collection[0].format()
        else:
            result['component_path'] = component_path
        result[
            'context_path'
        ] = f'{str_version(component["version"])} / {component["name"]}'
        return result

    def ui_hook(self, payload):
        '''
        Supply UI with entity data from options passed on in *payload*.
        '''
        try:
            return self._resolve_entity_paths(payload['event_data'])
        except PluginExecutionError as error:
            return {'error_message': str(error)}

    def run(self, store):
        '''
        Store entity data in the given *store*
        '''
        result = self._resolve_entity_paths(self.options['event_data'])
        keys = ['entity_id', 'entity_type', 'component_path', 'is_sequence']
        for k in keys:
            if result.get(k):
                store[k] = result.get(k)
                self.logger.debug(f"{store[k]} stored in {k}.")
