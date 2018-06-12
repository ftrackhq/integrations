# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import os
import re
import hiero
import logging
import ftrack_api
import time
import unicodedata



FTRACK_SHOW_PATH = os.path.join(
    '{ftrack_project}',
    '{ftrack_asset}',
    '{ftrack_component}'
)

FTRACK_SHOT_PATH = os.path.join(
    '{ftrack_project}',
    '{ftrack_sequence}',
    '{ftrack_shot}',
    '{ftrack_asset}',
    '{ftrack_component}'
)


class FtrackProcessorError(Exception):
    pass


class FtrackProcessorValidationError(FtrackProcessorError):
    pass


class FtrackBase(object):
    '''
    wrap ftrack functionalities and methods
    '''

    ingored_locations = [
        'ftrack.server',
        'ftrack.review',
        'ftrack.origin',
        'ftrack.unmanaged',
        'ftrack.connect'
    ]
    session = ftrack_api.Session(auto_connect_event_hub=False)
    illegal_character_substitute = '_'
    _components = {}

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

    def timeStampString(self, localtime):
        return time.strftime('%Y/%m/%d %X', localtime)

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

        if isinstance(value, str):
            value = value.decode('utf-8')

        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
        value = re.sub('[^\w\.-]', self.illegal_character_substitute, value)
        return unicode(value.strip().lower())

    @property
    def hiero_version_touple(self):
        return (
            hiero.core.env['VersionMajor'],
            hiero.core.env['VersionMinor'],
            hiero.core.env['VersionRelease'].split('v')[-1]
        )

    @property
    def ftrack_location(self):
        result = self.session.pick_location()
        return result

    @property
    def ftrack_origin_location(self):
        return self.session.query(
            'Location where name is "ftrack.origin"'
        ).one()

    @property
    def ftrack_server_location(self):
        return self.session.query(
            'Location where name is "ftrack.server"'
        ).one()


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

    def set_export_root(self):
        self.properties()['exportRoot'] = self.ftrack_location.accessor.prefix

    def resolve_ftrack_project(self, task):
        return self.sanitise_for_filesystem(task.projectName())

    def resolve_ftrack_sequence(self, task):
        trackItem = task._item
        return self.sanitise_for_filesystem(trackItem.name().split('_')[0])

    def resolve_ftrack_shot(self, task):
        trackItem = task._item

        if not isinstance(trackItem, hiero.core.Sequence):
            return self.sanitise_for_filesystem(trackItem.name().split('_')[1])
        else:
            return self.sanitise_for_filesystem(trackItem.name())

    def resolve_ftrack_asset(self, task):
        return self.sanitise_for_filesystem(self.properties()['ftrack']['asset_name'])

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
            '{ftrack_component}',
            'Ftrack component name.',
            lambda keyword, task: self.resolve_ftrack_component(task)
        )

