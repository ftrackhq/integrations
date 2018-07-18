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


current_ftrack_location = session.pick_location()

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

  if not hasattr(VersionScanner, '_default_filterVersion'):
    VersionScanner._default_filterVersion = VersionScanner.filterVersion
    VersionScanner.filterVersion = ftrack_filter_version

  if not hasattr(VersionScanner, '_default_createClip'):
    VersionScanner._default_createClip = VersionScanner.createClip
    VersionScanner.createClip = ftrack_create_clip

  VersionScanner._ftrack_component_reference = []


# Utility functions
def get_ftrack_tag(clip):
  # tags are stored in the source clip
  existingTag = None

  for tag in clip.tags():
    if tag.metadata().hasKey('tag.provider') and tag.metadata()['tag.provider'] == 'ftrack':
      existingTag = tag
      break

  if not existingTag:
      return False

  logger.info('get_ftrack_tag {}:{}'.format(clip, existingTag))
  return existingTag


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
  logger.info('add_clip_as_version:{}'.format(clip))

  component_id = has_tag.metadata()['component_id']
  # see which our index is
  versionIndex = ftrack_component_reference.index(component_id)
  targetBinIndex = -1

  logger.info('version index {}'.format(versionIndex))

  # Try to find the closed version that already exists in the bin
  binIndex = 0
  for v in binItem.items():
    c = v.item()
    bin_has_tag = get_ftrack_tag(c)
    if not bin_has_tag:
      return

    bin_component_id = bin_has_tag.metadata()['component_id']

    try:
      clipIndex = ftrack_component_reference.index(bin_component_id)
      if clipIndex >= versionIndex:
        targetBinIndex = binIndex
        break
    except:
      pass

    binIndex += 1

  version = hiero.core.Version(clip)
  logger.info('adding to bin item: {} as index {}'.format(version, targetBinIndex))

  binItem.addVersion(version, targetBinIndex)
  return version


# Overrides
def ftrack_find_version_files(scannerInstance, version):
  clip = version.item()
  ftrack_tag = get_ftrack_tag(clip)
  logger.debug('ftrack_find_version_files: {}: {}'.format(version, ftrack_tag))

  if not ftrack_tag:
    return scannerInstance._default_findVersionFiles(scannerInstance, version)

  location = session.pick_location()
  component_id = ftrack_tag.metadata()['component_id']
  component = session.get('Component', component_id)
  component_name = component['name']
  asset = component['version']['asset']

  unsorted_components = session.query(
    'select name, version.version from Component where version.asset.id is {} and name is {}'.format(
      asset['id'], component_name)
  ).all()
  sorted_components = sorted(unsorted_components, key=lambda k: int(k['version']['version']))

  # set paths to an array of dimension of max version

  max_version = sorted_components[-1]['version']['version']
  paths = [None]*max_version
  scannerInstance._ftrack_component_reference = [None]*max_version

  for component in sorted_components:
    component_avaialble = session.pick_location(component)
    if component_avaialble:
      component_version = component['version']['version'] - 1  # lists starts from 0, so version 1 should be first
      path = location.get_filesystem_path(component).split()[0]
      scannerInstance._ftrack_component_reference[component_version] = component

  hieroOrderedVersions = scannerInstance._ftrack_component_reference[::-1]

  # Prune out any we already have
  binitem = version.parent()
  filtered_paths = filter(lambda v : scannerInstance.filterVersion(binitem, v), hieroOrderedVersions)
  logger.debug('ftrack_find_version_files:result {}'.format(filtered_paths))
  return filtered_paths


def ftrack_filter_version(scannerInstance, binitem, newVersionFile):
    # We have to see if anything else in the bin has this ref
    logger.info('ftrack_filter_version : {}:{}'.format(binitem, newVersionFile))

    bin_ftrack_tag = get_ftrack_tag(binitem.activeItem())
    if not bin_ftrack_tag:
        return scannerInstance._default_filterVersion(binitem, newVersionFile)

    for version in binitem.items():
      item = version.item()
      ftrack_tag = get_ftrack_tag(item)
      if ftrack_tag:
          component_id = ftrack_tag.metadata()['component_id']
          if component_id == newVersionFile['id']:
              logger.info('filtered : {} : False'.format(newVersionFile))
              return False
    return True


def ftrack_create_clip(scannerInstance, newFilename):
    logger.info('ftrack_create_clip : {}'.format(newFilename))

    if newFilename in scannerInstance._ftrack_component_reference:
        is_available = session.pick_location(newFilename)
        if not is_available:
            return

        filepath = current_ftrack_location.get_filesystem_path(newFilename).split()[0]
        logger.debug('ftrack_create_clip:result {}'.format(filepath))
        return hiero.core.Clip(filepath)
    else:
        return scannerInstance._default_createClip(newFilename)


def ftrack_insert_clips(scannerInstance, binItem, clips):
    logger.info('ftrack_insert_entity_clips: {}'.format(clips))

    entities = []
    non_entities = []

    newVersions = []

    for c in clips:
        has_tags = get_ftrack_tag(c)
        logger.info('ftrack_insert_entity_clips: {}:{}'.format(c, has_tags))

        if not has_tags:
            non_entities.append(c)
        else:
            logger.info('ftrack_insert_entity_clips: {}'.format(c))
            entities.append(c)

    newVersions.extend(scannerInstance._default_insertClips(binItem, non_entities))

    for c in entities:
        v = add_clip_as_version(c, binItem, scannerInstance._ftrack_component_reference)
        newVersions.append(v)

    scannerInstance._ftrack_component_reference = []

    return newVersions


