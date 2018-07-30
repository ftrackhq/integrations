import logging
from hiero.core import NamingScheme

from ftrack_connect_nuke_studio_beta.overrides.version_scanner import get_ftrack_tag

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def register_naming_overrides():
    # Enable this to activate the custom naming example
    # Note: Do not remove 'staticmethod' from the assignment.
    NamingScheme.clipName = staticmethod(ftrack_clipName)
    NamingScheme.versionName = staticmethod(ftrack_versionName)
    NamingScheme.rootName = staticmethod(ftrack_rootName)


def ftrack_clipName(clip):
    tag = get_ftrack_tag(clip)
    logger.info('resolving clip {} has tag {}'.format(clip, tag))
    return NamingScheme.default_clipName(clip)


def ftrack_versionName(clip):
    tag = get_ftrack_tag(clip)
    logger.info('resolving version {} has tag {}'.format(clip, tag))
    return NamingScheme.default_versionName(clip)


def ftrack_rootName(clip):
    tag = get_ftrack_tag(clip)
    logger.info('resolving root {} has tag {}'.format(clip, tag))
    return NamingScheme.default_rootName(clip)
