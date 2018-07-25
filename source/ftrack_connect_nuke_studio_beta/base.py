import logging
import time
import re
import unicodedata
import logging
logger = logging.getLogger(__name__)

import hiero

from ftrack_connect.session import get_shared_session

# Disable file path creation from NS
def disable_path_creation(args):
    pass
hiero.core.util.filesystem.makeDirs = disable_path_creation


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
    illegal_character_substitute = '_'
    path_separator = '/'

    _components = {}

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)

    @property
    def session(self):
        return get_shared_session()

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
