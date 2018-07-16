import os
import re
import logging
import glob
from hiero.core.VersionScanner import VersionScanner
from ftrack_connect.session import get_shared_session

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def register_versioning_overrides():

  logger.debug('register_versioning_overrides')

  # We want to redefine some of the methods of VersionScanner, but may still need to use the default functionality within our custom methods.
  # Therefore, we need to save a reference to the default methods, and then we will be able to call them from ours.
  if not hasattr(VersionScanner, "_default_findVersionFiles"):
    VersionScanner._default_findVersionFiles =  VersionScanner.findVersionFiles
    VersionScanner.findVersionFiles = ftrack_find_version_files

  if not hasattr(VersionScanner, '_default_filterVersion'):
    VersionScanner._default_filterVersion = VersionScanner.filterVersion
    VersionScanner.filterVersion = ftrack_filter_version

  if not hasattr(VersionScanner, '_default_createClip'):
    VersionScanner._default_createClip = VersionScanner.createClip
    VersionScanner.createClip = ftrack_create_clip

  if not hasattr(VersionScanner, '_default_insertClips'):
    VersionScanner._default_insertClips = VersionScanner.insertClips
    VersionScanner.insertClips = ftrack_insert_clips

  VersionScanner._entityVersions = []



def ftrack_find_version_files(scannerInstance, version):
  logger.debug('ftrack_find_version_files')
  clip = version.item()
  logger.info(clip)
  logger.info(clip.tags())
  pass


def ftrack_filter_version(scannerInstance, binitem, newVersionFile):
  clip = binitem.item()

  if not hasattr(binitem.item(), 'tags'):
    return
  existingTag = None

  for tag in clip.tags():
    if tag.metadata().hasKey('tag.provider') and tag.metadata()['tag.provider'] == 'ftrack':
      existingTag = tag
      break

  logger.debug('ftrack_find_version_files: {0}'.format(existingTag.metadata()))
  pass


def ftrack_create_clip(scannerInstance, newFilename):
  logger.debug('ftrack_find_version_files')
  pass


def ftrack_insert_clips(scannerInstance, binItem, clips):
  logger.debug('ftrack_find_version_files')
  pass