# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import os
import hiero
from ftrack_connect_nuke_studio_beta.base import FtrackBase
from ftrack_connect_nuke_studio_beta.template import match, get_project_template

FTRACK_SHOW_PATH = FtrackBase.path_separator.join([
    '{ftrack_project}',
    '{ftrack_asset}',
    '{ftrack_version}',
    '{ftrack_component}'
])

FTRACK_SHOT_PATH = FtrackBase.path_separator.join([
    '{ftrack_project}',
    '{ftrack_sequence}',
    '{ftrack_shot}',
    '{ftrack_asset}',
    '{ftrack_version}',
    '{ftrack_component}'
])


class FtrackProcessorError(Exception):
    pass


class FtrackProcessorValidationError(FtrackProcessorError):
    pass


class FtrackBasePreset(FtrackBase):
    def __init__(self, name, properties, **kwargs):
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
        properties = self.properties()
        properties.setdefault('ftrack', {})
        # add placeholders for default processor
        self.properties()['ftrack']['project_schema'] = 'Film Pipeline'
        self.properties()['ftrack']['opt_publish_reviewable'] = True
        self.properties()['ftrack']['opt_publish_thumbnail'] = False

    def set_export_root(self):
        self.properties()['exportRoot'] = self.ftrack_location.accessor.prefix

    def resolve_ftrack_project(self, task):
        return self.sanitise_for_filesystem(task.projectName())

    def resolve_ftrack_sequence(self, task):
        trackItem = task._item
        template = get_project_template(task._project)

        if not isinstance(trackItem, hiero.core.Sequence):
            return self.sanitise_for_filesystem(trackItem.name().split('_')[0])
        else:
            return self.sanitise_for_filesystem(trackItem.name())

    def resolve_ftrack_shot(self, task):
        trackItem = task._item
        template = get_project_template(task._project)

        if not isinstance(trackItem, hiero.core.Sequence):
            return self.sanitise_for_filesystem(trackItem.name().split('_')[1])
        else:
            return self.sanitise_for_filesystem(trackItem.name())

    def resolve_ftrack_asset(self, task):
        asset_name = self.properties()['ftrack'].get('asset_name')
        if not asset_name:
            asset_name = task._preset.properties()['ftrack']['asset_name']
        return self.sanitise_for_filesystem(asset_name)

    def resolve_ftrack_version(self, task):

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
        component_name = self.sanitise_for_filesystem(task._preset.name())
        extension = self.properties()['ftrack']['component_pattern']
        component_full_name = '{0}{1}'.format(component_name, extension)
        return component_full_name.lower()

    def addFtrackResolveEntries(self, resolver):

        resolver.addResolver(
            '{ftrack_project}',
            'Ftrack project name.',
            lambda keyword, task: self.resolve_ftrack_project(task)
        )

        resolver.addResolver(
            '{ftrack_sequence}',
            'Ftrack sequence name.',
            lambda keyword, task: self.resolve_ftrack_sequence(task)
        )

        resolver.addResolver(
            '{ftrack_shot}',
            'Ftrack shot name.',
            lambda keyword, task: self.resolve_ftrack_shot(task)
        )

        resolver.addResolver(
            '{ftrack_asset}',
            'Ftrack asset name.',
            lambda keyword, task: self.resolve_ftrack_asset(task)
        )

        resolver.addResolver(
            '{ftrack_version}',
            'Ftrack version.',
            lambda keyword, task: self.resolve_ftrack_version(task)
        )


        resolver.addResolver(
            '{ftrack_component}',
            'Ftrack component name.',
            lambda keyword, task: self.resolve_ftrack_component(task)
        )

