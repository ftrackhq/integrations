import os
import re
import logging
import glob
from hiero.core.VersionScanner import VersionScanner
from ftrack_connect.session import get_shared_session

session = get_shared_session()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def register_versioning_overrides():

  logger.debug('register_versioning_overrides')

  # We want to redefine some of the methods of VersionScanner, but may still need to use the default functionality within our custom methods.
  # Therefore, we need to save a reference to the default methods, and then we will be able to call them from ours.
  if not hasattr(VersionScanner, '_default_findVersionFiles'):
    VersionScanner._default_findVersionFiles = VersionScanner.findVersionFiles
    VersionScanner.findVersionFiles = ftrack_find_version_files

  if not hasattr(VersionScanner, '_default_insertClips'):
    VersionScanner._default_insertClips = VersionScanner.insertClips
    VersionScanner.insertClips = ftrack_insert_clips

  VersionScanner._ftrack_component_reference = []


def get_ftrack_tag(clip):
  # tags are stored in the source clip
  existingTag = None

  for tag in clip.tags():
    if tag.metadata().hasKey('tag.provider') and tag.metadata()['tag.provider'] == 'ftrack':
      existingTag = tag
      break

  logger.info('Checking tags  : {} - {}'.format(clip, existingTag))

  if not existingTag:
      return False

  return existingTag


def ftrack_insert_clips(scannerInstance, binItem, clips):
  entities = []
  nonEntities = []

  newVersions = []

  for c in clips:
    has_tags = get_ftrack_tag(c)
    if not has_tags:
      nonEntities.append(c)

  scannerInstance._ftrack_component_reference = []

  newVersions.extend(scannerInstance._default_insertClips(binItem, nonEntities))
  return newVersions


def ftrack_find_version_files(scannerInstance, version):
  clip = version.item()
  ftrack_tag = get_ftrack_tag(clip)
  logger.debug('ftrack_find_version_files: {}: {}'.format(version, ftrack_tag))

  if not ftrack_tag:
    return VersionScanner._default_findVersionFiles(scannerInstance, version)

  location = session.pick_location()
  component_id = ftrack_tag.metadata()['component_id']
  component = session.get('Component', component_id)
  component_name = component['name']
  asset = component['version']['asset']
  logger.info(asset)
  paths = []

  unsorted_compomnents = session.query(
    'select name, version.version from Component where version.asset.id is {} and name is {}'.format(
      asset['id'], component_name)
  ).all()
  sorted_components = sorted(unsorted_compomnents, key=lambda k: int(k['version']['version']))

  logger.info(sorted_components)

  paths = []
  for component in sorted_components:
    component_avaialble = session.pick_location(component)

    if component_avaialble:
      logger.info('VERSION: {} component: {}'.format(component['version']['version'], component))

      path = location.get_filesystem_path(component)
      paths.append(path)

  return paths
