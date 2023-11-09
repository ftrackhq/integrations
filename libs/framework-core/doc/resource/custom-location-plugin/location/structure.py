# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import sys
import os
import re
import unicodedata
import logging
import traceback

from collections import OrderedDict

import ftrack_api.symbol
import ftrack_api.structure.base

STUDIO_PUBLISH_FOLDER = "PUBLISH"


class Structure(ftrack_api.structure.base.Structure):
    '''
    Custom structure publishing to "_PUBLISH" folder beneath shot.
    '''

    def __init__(
        self, project_versions_prefix=None, illegal_character_substitute='_'
    ):
        super(Structure, self).__init__()
        self.logger = logging.getLogger(
            'com.ftrack.integrations.tutorials.custom-location-plugin.location.Structure'
        )
        self.project_versions_prefix = project_versions_prefix
        self.illegal_character_substitute = illegal_character_substitute
        self.resolvers = OrderedDict(
            {
                'FileComponent': self._resolve_filecomponent,
                'SequenceComponent': self._resolve_sequencecomponent,
                'ContainerComponent': self._resolve_containercomponent,
                'AssetVersion': self._resolve_version,
                'Asset': self._resolve_asset,
                'Task': self._resolve_task,
                'Project': self._resolve_project,
                'ContextEntity': self._resolve_context_entity,
            }
        )

    def sanitise_for_filesystem(self, value):
        '''Return *value* with illegal filesystem characters replaced.

        An illegal character is one that is not typically valid for filesystem
        usage, such as non ascii characters, or can be awkward to use in a
        filesystem, such as spaces. Replace these characters with
        the character specified by *illegal_character_substitute* on
        initialisation. If no character was specified as substitute then return
        *value* unmodified.

        '''
        if self.illegal_character_substitute is None:
            return value

        value = unicodedata.normalize('NFKD', str(value)).encode(
            'ascii', 'ignore'
        )
        value = re.sub(
            '[^\w\.-]',
            self.illegal_character_substitute,
            value.decode('utf-8'),
        )
        return str(value.strip().lower())

    def _resolve_project(self, project, context=None):
        '''Return resource identifier for *project*.'''
        # Base on project name
        return [self.sanitise_for_filesystem(project['name'])]

    def _resolve_context_entity(self, entity, context=None):
        '''Return resource identifier parts from general *entity*.'''

        error_message = (
            'Entity {0!r} must be supported (have a link), be committed and have'
            ' a parent context.'.format(entity)
        )

        if entity is ftrack_api.symbol.NOT_SET:
            raise ftrack_api.exception.StructureError(error_message)

        session = entity.session

        if not 'link' in entity:
            raise NotImplementedError(
                'Cannot generate resource identifier for unsupported '
                'entity {0!r}'.format(entity)
            )

        link = entity['link']

        if not link:
            raise ftrack_api.exception.StructureError(error_message)

        structure_names = [item['name'] for item in link[1:]]

        if 'project' in entity:
            project = entity['project']
        elif 'project_id' in entity:
            project = session.get('Project', entity['project_id'])
        else:
            project = session.get('Project', link[0]['id'])

        parts = self._resolve_project(project)

        if structure_names:
            for part in structure_names:
                parts.append(self.sanitise_for_filesystem(part))
        elif self.project_versions_prefix:
            # Add *project_versions_prefix* if configured and the version is
            # published directly under the project.
            parts.append(
                self.sanitise_for_filesystem(self.project_versions_prefix)
            )

        return parts

    def _resolve_task(self, task, context=None):
        '''Build resource identifier for *task*.'''
        # Resolve parent context
        parts = self._resolve_context_entity(task['parent'], context=context)
        # TODO: Customise were task work files go
        # Base on task name, and use underscore instead of whitespaces
        parts.append(
            self.sanitise_for_filesystem(task['name'].replace(' ', '_'))
        )
        return parts

    def _resolve_asset(self, asset, context=None):
        '''Build resource identifier for *asset*.'''
        # Resolve parent context
        parts = self._resolve_context_entity(asset['parent'], context=context)
        # Framework guide customisation - publish to shot/asset "publish" subfolder
        parts.append(STUDIO_PUBLISH_FOLDER)
        # Base on its name
        parts.append(self.sanitise_for_filesystem(asset['name']))
        return parts

    def _format_version(self, number):
        '''Return a formatted string representing version *number*.'''
        return 'v{0:03d}'.format(number)

    def _resolve_version(self, version, component=None, context=None):
        '''Get resource identifier for *version*.'''

        error_message = 'Version {0!r} must be committed and have a asset with parent context.'.format(
            version
        )

        if version is ftrack_api.symbol.NOT_SET and component:
            version = component.session.get(
                'AssetVersion', component['version_id']
            )

        if version is ftrack_api.symbol.NOT_SET or (
            not component is None and version in component.session.created
        ):
            raise ftrack_api.exception.StructureError(error_message)

        # Create version resource identifier from asset and version number
        version_number = self._format_version(version['version'])
        parts = self._resolve_asset(version['asset'], context=context)
        parts.append(self.sanitise_for_filesystem(version_number))

        return parts

    def _resolve_sequencecomponent(self, sequencecomponent, context=None):
        '''Get resource identifier for *sequencecomponent*.'''
        # Create sequence expression for the sequence component and add it
        # to the parts.
        parts = self._resolve_version(
            sequencecomponent['version'],
            component=sequencecomponent,
            context=context,
        )
        sequence_expression = self._get_sequence_expression(sequencecomponent)
        parts.append(
            '{0}.{1}{2}'.format(
                self.sanitise_for_filesystem(sequencecomponent['name']),
                sequence_expression,
                self.sanitise_for_filesystem(sequencecomponent['file_type']),
            )
        )
        return parts

    def _resolve_container(self, component, container, context=None):
        '''Get resource identifier for *container*, based on the *component*
        supplied.'''
        container_path = self.get_resource_identifier(
            container, context=context
        )
        if container.entity_type in ('SequenceComponent',):
            # Strip the sequence component expression from the parent
            # container and back the correct filename, i.e.
            # /sequence/component/sequence_component_name.0012.exr.
            name = '{0}.{1}{2}'.format(
                container['name'], component['name'], component['file_type']
            )
            parts = [
                os.path.dirname(container_path),
                self.sanitise_for_filesystem(name),
            ]

        else:
            # Container is not a sequence component so add it as a
            # normal component inside the container.
            name = component['name'] + component['file_type']
            parts = [container_path, self.sanitise_for_filesystem(name)]
        return parts

    def _resolve_filecomponent(self, filecomponent, context=None):
        '''Get resource identifier for file component.'''
        container = filecomponent['container']
        if container:
            parts = self._resolve_container(
                filecomponent, container, context=context
            )
        else:
            # File component does not have a container, construct name from
            # component name and file type.
            parts = self._resolve_version(
                filecomponent['version'],
                component=filecomponent,
                context=context,
            )
            name = filecomponent['name'] + filecomponent['file_type']
            parts.append(self.sanitise_for_filesystem(name))
        return parts

    def _resolve_containercomponent(self, containercomponent, context=None):
        '''Get resource identifier for *containercomponent*.'''
        # Get resource identifier for container component
        # Add the name of the container to the resource identifier parts.
        parts = self._resolve_version(
            containercomponent['version'],
            component=containercomponent,
            context=context,
        )
        parts.append(self.sanitise_for_filesystem(containercomponent['name']))
        return parts

    def get_resource_identifier(self, entity, context=None):
        '''Return a resource identifier for supplied *entity*.

        *context* can be a mapping that supplies additional information, but
        is unused in this implementation.


        Raise a :py:exc:`ftrack_api.exeption.StructureError` if *entity* is a
        component not attached to a committed version/asset with a parent
        context, or if entity is not a proper Context.

        '''

        resolver_fn = self.resolvers.get(
            entity.entity_type, self._resolve_context_entity
        )

        parts = resolver_fn(entity, context=context)

        return self.path_separator.join(parts)
