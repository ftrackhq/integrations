# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import logging
import hiero
from ftrack_connect_nuke_studio_beta.base import FtrackBase
from ftrack_connect_nuke_studio_beta.template import match, get_project_template
import ftrack_connect_nuke_studio_beta.exception


logger = logging.getLogger(__name__)

FTRACK_SHOW_PATH = FtrackBase.path_separator.join([
    '{ftrack_project}',
    '{ftrack_asset}',
    '{ftrack_version}',
    '{ftrack_component}'
])


FTRACK_SHOT_PATH = FtrackBase.path_separator.join([
    '{ftrack_project}',
    '{ftrack_context}',
    '{ftrack_asset}',
    '{ftrack_version}',
    '{ftrack_component}'
])


class FtrackProcessorError(Exception):
    ''' Base ftrack processor error. '''


class FtrackProcessorValidationError(FtrackProcessorError):
    ''' Ftrack processor validation error. '''


def lock_reference_ftrack_project(project):
    for sequence in project.sequences():
        for tag in sequence.tags():
            if tag.name() == 'ftrack.project_reference' and tag.metadata().hasKey('ftrack.project_reference.id'):
                tag.metadata().setValue('ftrack.project_reference.locked', str(1))


def get_reference_ftrack_project(project):
    '''Return ftrack project reference stored on *project* and whether is locked.'''
    ftrack_project_id = None
    is_project_locked = False
    # Fetch the templates from tags on sequences on the project.
    # This is a workaround due to that projects do not have tags or metadata.
    for sequence in project.sequences():
        logger.info('Getting tags from: {}'.format(sequence))
        for tag in sequence.tags():
            logger.info('TAG:{}'.format(tag.metadata()))
            if tag.name() == 'ftrack.project_reference':
                ftrack_project_id = tag.metadata().value('ftrack.project_reference.id')
                is_project_locked = int(tag.metadata().value('ftrack.project_reference.locked'))
                logger.debug('Found project_id reference : {} on {} is locked {}'.format(
                    ftrack_project_id, project, is_project_locked)
                )
                break

        if ftrack_project_id:
            break

    return ftrack_project_id, is_project_locked


def set_reference_ftrack_project(project, project_id):
    '''Set *project* tags to ftrack *project_id* if doesn't exist.'''
    for sequence in project.sequences():

        for tag in sequence.tags():
            for _tag in sequence.tags()[:]:
                if (
                        _tag.name() == 'ftrack.project_reference' and
                        not _tag.metadata().value('ftrack.project_reference.locked')
                ):
                    logger.info('removing tag: {}'.format(_tag))
                    sequence.removeTag(_tag)

            tag = hiero.core.Tag('ftrack.project_reference')
            logger.info('Setting tag :{} to {}'.format(tag, project_id))
            tag.metadata().setValue('ftrack.project_reference.id', project_id)
            tag.metadata().setValue('ftrack.project_reference.locked', str(0))
            # tag.setVisible(False)

            sequence.addTag(tag)


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

        self.properties()['ftrack']['opt_publish_reviewable'] = True
        self.properties()['ftrack']['opt_publish_thumbnail'] = False

    def set_export_root(self):
        '''Set project export root to current ftrack location's accessor prefix.'''
        self.properties()['exportRoot'] = self.ftrack_location.accessor.prefix

    def resolve_ftrack_project(self, task):
        ''' Return project name for the given *task*. '''
        project = task._project
        ftrack_project_id = get_reference_ftrack_project(project)
        ftrack_project = self.session.get('Project', ftrack_project_id)
        return self.sanitise_for_filesystem(ftrack_project['name'])

    def resolve_ftrack_context(self, task):
        ''' Return context for the given *task*.

        data returned from this resolver are expressed as:
        <object_type>:<object_name>|<object_type>:<object_name>|....
        '''
        track_item = task._item
        template = get_project_template(task._project)

        if not isinstance(track_item, hiero.core.Sequence):
            data = []
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

    def resolve_ftrack_asset(self, task):
        ''' Return asset for the given *task*.'''
        asset_name = self.properties()['ftrack'].get('asset_name')
        if not asset_name:
            asset_name = task._preset.properties()['ftrack']['asset_name']
        return self.sanitise_for_filesystem(asset_name)

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
            '{ftrack_project}',
            'Ftrack project name.',
            lambda keyword, task: self.resolve_ftrack_project(task)
        )

        resolver.addResolver(
            '{ftrack_context}',
            'Ftrack context name.',
            lambda keyword, task: self.resolve_ftrack_context(task)
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

