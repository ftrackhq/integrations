# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import time
import re
import unicodedata
import logging
logger = logging.getLogger(__name__)

import hiero

from ftrack_connect_nuke_studio.session import get_shared_session


class FtrackBase(object):
    '''
    wrap ftrack functionalities and methods
    '''

    ingored_locations = [
        'ftrack.server',
        'ftrack.review',
        'ftrack.origin',
        'ftrack.unmanaged',
        'ftrack.connect',
        'ftrack.perforce-scenario'
    ]
    illegal_character_substitute = '_'
    path_separator = '/'

    _components = {}

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    @property
    def session(self):
        '''Return ftrack session.'''
        return get_shared_session()

    def timeStampString(self, localtime):
        '''Return stringified *localtime*.'''
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

        if isinstance(value, bytes):
            value = value.decode('utf-8')

        value = unicodedata.normalize('NFKD', value)
        value = re.sub(u'[^\w\.-]', self.illegal_character_substitute, value)
        return value.strip().lower()

    @property
    def hiero_version_tuple(self):
        '''Return current hiero version.'''
        return (
            hiero.core.env['VersionMajor'],
            hiero.core.env['VersionMinor'],
            hiero.core.env['VersionRelease'].split('v')[-1]
        )

    @property
    def ftrack_location(self):
        '''Return current ftrack location.'''
        result = self.session.pick_location()
        return result