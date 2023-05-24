# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import os
import logging
import hiero
import nuke
import datetime
from ftrack_connect_nuke_studio.base import FtrackBase
from ftrack_connect_nuke_studio.template import match, get_project_template
import ftrack_connect_nuke_studio.exception

logger = logging.getLogger(__name__)


FTRACK_PROJECT_STRUCTURE = FtrackBase.path_separator.join([
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
            message = (
                '<h2>"{0}" is an invalid location for Nuke Studio to work with.</h2>' 
                'Please setup a centralised storage scenario or custom location and retry.<br/>'
                'For more information on storage and location configurations, please see our'
                '<a href=https://help.ftrack.com/en/articles/1040436-configuring-file-storage> <b>help</b></a>'
                ''.format(
                    current_location['name']
                )
            )

            nuke.message(message)
            raise FtrackProcessorError(message)

        self.set_export_root()
        self._timeStamp = datetime.datetime.now()

        if not properties.get('ftrack'):
            self.set_ftrack_properties(properties)

    def timeStamp(self):
        '''timeStamp(self)
        Returns the datetime object from time of task creation'''
        return self._timeStamp

    def set_ftrack_properties(self, properties):
        ''' Ensure and extend common ftrack *properties* . '''
        properties = self.properties()
        properties.setdefault('ftrack', {})

        self.properties()['ftrack']['opt_publish_reviewable'] = True
        self.properties()['ftrack']['opt_publish_thumbnail'] = False
        self.properties()['useAssets'] = False
        self.properties()['keepNukeScript'] = True

    def set_export_root(self):
        '''Set project export root to current ftrack location's accessor prefix.'''
        self.properties()['exportRoot'] = self.ftrack_location.accessor.prefix

    def resolve_ftrack_project_structure(self, task):
        ''' Return context for the given *task*.

        data returned from this resolver are expressed as:
        <object_type>:<object_name>|<object_type>:<object_name>|....
        '''

        ''' Return project name for the given *task*. '''
        project_id = os.getenv('FTRACK_CONTEXTID')
        ftrack_project = self.session.get('Project', project_id)
        ftrack_project_name = ftrack_project['full_name']

        track_item = task._item
        template = get_project_template(task._project)

        # Inject project as first item.
        data = ['Project:{}'.format(ftrack_project_name)]

        if not isinstance(track_item, hiero.core.Sequence):
            try:
                results = match(track_item, template)
            except ftrack_connect_nuke_studio.exception.TemplateError:
                # we can happly return None as if the validation does not goes ahead
                # the shot won't be created.
                return None

            for result in results:
                sanitised_result = self.sanitise_for_filesystem(result['name'])
                composed_result = '{}:{}'.format(result['object_type'], sanitised_result)
                data.append(composed_result)

        result_data = '|'.join(data)
        return result_data

    def resolve_ftrack_version(self, task):
        ''' Return version for the given *task*.'''
        version = 1  # first version is 1

        if not self._components:
            return 'v{:03d}'.format(version)

        has_data = self._components.get(
            task._item.parent().name(), {}
        ).get(
            task._item.name(), {}
        ).get(task.component_name())

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

