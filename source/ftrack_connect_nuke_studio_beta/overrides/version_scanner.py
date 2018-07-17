import os
import re
import logging
import glob

import hiero
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


def add_clip_as_version(clip, binItem, ftrack_component_reference):
  """

  Adds the supplied clip to the supplied bin item as a new Version. It takes
  care that the clip is placed at the right index in the bin so that versions
  are correctly sorted. This is done by comparing all other Versions already
  present to the supplied entityVersionList to determine the correct index.

  @param entityVersionsList list, This should be a sorted list of the entity
  references for every version of the entity the clip is representing. Such a
  list can be retrieved from Entity.getVersions(asRefs=True, asList=True)

  @return hiero.core.Version, the newly created Version object

  """
  has_tag = get_ftrack_tag(clip)
  if not has_tag:
    return
  component_id = has_tag.metadata()['component_id']
  # see which our index is
  versionIndex = ftrack_component_reference.index(component_id)
  targetBinIndex = -1

  # Try to find the closed version that already exists in the bin
  binIndex = 0
  for v in binItem.items():
    c = v.item()
    try:
      clipIndex = ftrack_component_reference.index(component_id)
      if clipIndex >= versionIndex:
        targetBinIndex = binIndex
        break
    except:
      pass

    binIndex += 1

  version = hiero.core.Version(clip)
  binItem.addVersion(version, targetBinIndex)
  return version


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
  non_entities = []

  newVersions = []

  for c in clips:
    has_tags = get_ftrack_tag(c)
    if not has_tags:
      non_entities.append(c)
    else:
      entities.append(c)

  newVersions.extend(scannerInstance._default_insertClips(binItem, non_entities))

  for c in entities:
    v = add_clip_as_version(c, binItem, scannerInstance._ftrack_component_reference)
    newVersions.append(v)

  scannerInstance._ftrack_component_reference = []
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
      VersionScanner._ftrack_component_reference.append(component)
      path = location.get_filesystem_path(component)
      paths.append(path)

  return paths
