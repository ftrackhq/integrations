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
  if not hasattr(VersionScanner, "_default_findVersionFiles"):
    VersionScanner._default_findVersionFiles = VersionScanner.findVersionFiles
    VersionScanner.findVersionFiles = ftrack_find_version_files

  VersionScanner._entityVersions = []


def ftrack_insert_versions(self, binitem, versionFiles):
  newClips = []
  for newFilename in versionFiles:
    newClip = self.createClip(newFilename)

    if newClip is not None:
      newClips.append(newClip)

  return self.insertClips(binitem, newClips)


def ftrack_find_version_files(scannerInstance, version):
  logger.debug('ftrack_find_version_files: {}'.format(str(version)))
  clip = version.item()
  location = session.pick_location()
  existingTag = None

  for tag in clip.tags():
    if tag.metadata().hasKey('tag.provider') and tag.metadata()['tag.provider'] == 'ftrack':
      existingTag = tag
      break

  if not existingTag:
    return []

  component_id = existingTag.metadata()['component_id']
  component = session.get('Component', component_id)
  component_name = component['name']
  versions = component['version']['asset']['versions']
  components = []
  for version in versions:
    logger.info('VERSION: {}'.format(version['version']))

    components = session.query(
      'Component where name is "{0}" and version.id is "{0}"'.format(
        component_name, version['id']
      )
    ).all()
    for component in components:
      component_avaialble = session.pick_location(component)

      if component_avaialble:
        components.append(component)

  return components
