# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import hiero
from ftrack_connect_nuke_studio_beta.base import FtrackBase
from ftrack_connect_nuke_studio_beta.template import match, get_project_template
import ftrack_connect_nuke_studio_beta.exception


FTRACK_SHOW_PATH = FtrackBase.path_separator.join([
    '{ftrack_project_structure} ',
    '{ftrack_version}',
    '{ftrack_component}'
])


FTRACK_SHOT_PATH = FtrackBase.path_separator.join([
    '{ftrack_project_structure}',
    '{ftrack_version}',
    '{ftrack_component}'
])


class FtrackProcessorError(Exception):
    ''' Base ftrack processor error. '''


class FtrackProcessorValidationError(FtrackProcessorError):
    ''' Ftrack processor validation error. '''


class FtrackBasePreset(FtrackBase):

    def __init__(self, name, properties, **kwargs):
        ''' Initialise class with *name* and *properties*, '''
        super(FtrackBasePreset, self).__init__(name, properties)
        current_location = self.ftrack_location
        if current_location['name'] in self.ingored_locations:
            raise FtrackProcessorError(
                '{0} is an invalid location. Please setup'
                ' a centralised storage scenario or custom location.'.format(
                    current_location['name']
                )
            )

        self.set_export_root()
        self.set_ftrack_properties(properties)

    def set_ftrack_properties(self, properties):
        ''' Ensure and extend common ftrack *properties* . '''
        properties = self.properties()
        properties.setdefault('ftrack', {})

        # add placeholders for default processor
        self.properties()['ftrack']['project_schema'] = 'Film Pipeline'
        self.properties()['ftrack']['opt_publish_reviewable'] = True
        self.properties()['ftrack']['opt_publish_thumbnail'] = False

    def set_export_root(self):
        '''Set project export root to current ftrack location's accessor prefix.'''
        self.properties()['exportRoot'] = self.ftrack_location.accessor.prefix

    def resolve_ftrack_project_structure(self, task):
        ''' Return context for the given *task*.

        data returned from this resolver are expressed as:
        <object_type>:<object_name>|<object_type>:<object_name>|....
        '''

        project_name = self.sanitise_for_filesystem(task.projectName())

        track_item = task._item
        template = get_project_template(task._project)

        if not isinstance(track_item, hiero.core.Sequence):
            data = ['Project:{}'.format(project_name)]
            try:
                results = match(track_item, template)
            except ftrack_connect_nuke_studio_beta.exception.TemplateError:
                # we can happly return None as if the validation does not goes ahead
                # the shot won't be created.
                return None

            for result in results:
                sanitised_result = self.sanitise_for_filesystem(result['name'])
                composed_result = '{}:{}'.format(result['object_type'], sanitised_result)
                data.append(composed_result)

            result_data = '|'.join(data)
            return result_data
        else:
            return self.sanitise_for_filesystem(track_item.name())

    def resolve_ftrack_version(self, task):
        ''' Return version for the given *task*.'''
        version = 1  # first version is 1

        if not self._components:
            return 'v{:03d}'.format(version)

        has_data = self._components.get(
            task._item.name(), {}
        ).get(task._preset.name())

        if not has_data:
            return 'v{:03d}'.format(version)

        version = str(has_data['component']['version']['version'])
        return 'v{:03d}'.format(version)

    def resolve_ftrack_component(self, task):
        ''' Return component for the given *task*.'''
        component_name = self.sanitise_for_filesystem(task._preset.name())
        extension = self.properties()['ftrack']['component_pattern']
        component_full_name = '{0}{1}'.format(component_name, extension)
        return component_full_name.lower()

    def addFtrackResolveEntries(self, resolver):
        ''' Add custom ftrack resolver in *resolver*. '''

        resolver.addResolver(
            '{ftrack_project_structure}',
            'Ftrack context contains Project, Episodes, Sequence and Shots.',
            lambda keyword, task: self.resolve_ftrack_project_structure(task)
        )

        resolver.addResolver(
            '{ftrack_version}',
            'Ftrack version contains Task, Asset and AssetVersion.',
            lambda keyword, task: self.resolve_ftrack_version(task)
        )

        resolver.addResolver(
            '{ftrack_component}',
            'Ftrack component name in AssetVersion.',
            lambda keyword, task: self.resolve_ftrack_component(task)
        )

