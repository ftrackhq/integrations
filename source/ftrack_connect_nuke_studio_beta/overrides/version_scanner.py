# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import logging

from QtExt import QtGui

import hiero
from hiero.core.VersionScanner import VersionScanner
from ftrack_connect.session import get_shared_session

session = get_shared_session()
logger = logging.getLogger(__name__)

current_ftrack_location = session.pick_location()


def register_versioning_overrides():

    logger.debug('register_versioning_overrides')

    # We want to redefine some of the methods of VersionScanner,
    # but may still need to use the default functionality within our custom methods.
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

    hiero.core.events.registerInterest('kShowContextMenu/kTimeline', customise_menu)


def customise_menu(event):
    actions = event.menu.actions()
    for action in actions:
        if action.text() in ['Version', 'Export...']:
            action.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoLight'))


def add_ftrack_build_tag(clip, component):
    version = component['version']

    existingTag = None
    for tag in clip.tags():
        if (
                tag.metadata().hasKey('tag.provider') and
                tag.metadata()['tag.provider'] == 'ftrack' and
                tag.metadata().hasKey('tag.component_name') and
                tag.metadata()['tag.component_name'] == component['name']
        ):
            existingTag = tag
            break

    if existingTag:
        return

    tag = hiero.core.Tag(
        'ftrack-reference-{0}'.format(component['name']),
        ':ftrack/image/default/ftrackLogoLight',
        False
    )
    tag.metadata().setValue('tag.provider', 'ftrack')
    tag.metadata().setValue('tag.component_id', component['id'])
    tag.metadata().setValue('tag.version_id', version['id'])
    tag.metadata().setValue('tag.version_number', str(version['version']))
    tag.metadata().setValue('tag.component_name', str(component['name']))

    # tag.setVisible(False)
    clip.addTag(tag)
    clip_name = '{}_v{:03}'.format(component['name'], component['version']['version'])
    clip.setName(clip_name)



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
    return existingTag


def add_clip_as_version(clip, binItem, ftrack_component_reference):
    has_tag = get_ftrack_tag(clip)
    component_id = has_tag.metadata()['component_id']
    component = session.get('Component', component_id)
    versionIndex = ftrack_component_reference.index(component)
    targetBinIndex = -1

    binIndex = 0
    for version in binItem.items():
        bin_clip = version.item()
        bin_clip_has_tag = get_ftrack_tag(bin_clip)
        bin_clip_component_id = bin_clip_has_tag.metadata()['component_id']
        bin_clip_component = session.get('Component', bin_clip_component_id)
        bin_clip_index = ftrack_component_reference.index(bin_clip_component)
        set_version_index =  bin_clip_index >= versionIndex
        try:
            if set_version_index:
                targetBinIndex = binIndex
                break
        except:
            pass
        binIndex += 1

    version = hiero.core.Version(clip)
    binItem.addVersion(version, targetBinIndex)
    return version


# Overrides
def ftrack_find_version_files(scannerInstance, version):
    clip = version.item()
    ftrack_tag = get_ftrack_tag(clip)

    if not ftrack_tag:
        return scannerInstance._default_findVersionFiles(scannerInstance, version)

    component_id = ftrack_tag.metadata()['component_id']
    component = session.get('Component', component_id)
    component_name = component['name']
    asset = component['version']['asset']

    unsorted_components = session.query(
        'select name, version.version from Component where version.asset.id is {} and name is {}'.format(
            asset['id'], component_name
        )
    ).all()
    sorted_components = sorted(unsorted_components, key=lambda k: int(k['version']['version']))

    # set paths to an array of dimension of max version

    scannerInstance._ftrack_component_reference = []

    for component in sorted_components:
        component_avaialble = session.pick_location(component)
        if component_avaialble:
            scannerInstance._ftrack_component_reference.append(component)

    hieroOrderedVersions = scannerInstance._ftrack_component_reference[::-1]

    # Prune out any we already have
    binitem = version.parent()
    filtered_paths = filter(lambda v : scannerInstance.filterVersion(binitem, v), hieroOrderedVersions)
    return filtered_paths


def ftrack_filter_version(scannerInstance, binitem, newVersionFile):
    # We have to see if anything else in the bin has this ref
    bin_ftrack_tag = get_ftrack_tag(binitem.items()[0].item()) # let's check if the first version has it...
    if not bin_ftrack_tag:
        return scannerInstance._default_filterVersion(binitem, newVersionFile)


    for version in binitem.items():
      item = version.item()
      ftrack_tag = get_ftrack_tag(item)
      if ftrack_tag:
          component_id = ftrack_tag.metadata()['component_id']
          if (
                  component_id == newVersionFile['id']
          ):
              return False
    return True


def ftrack_create_clip(scannerInstance, newFilename):
    if newFilename in scannerInstance._ftrack_component_reference:
        is_available = session.pick_location(newFilename)
        if not is_available:
            return

        filepath = current_ftrack_location.get_filesystem_path(newFilename).split()[0]
        clip = hiero.core.Clip(filepath)
        add_ftrack_build_tag(clip, newFilename)
        return clip
    else:
        return scannerInstance._default_createClip(newFilename)


def ftrack_insert_clips(scannerInstance, binItem, clips):
    entities = []
    non_entities = []
    newVersions = []

    for clip in clips:
        has_tags = get_ftrack_tag(clip)
        if not has_tags:
            non_entities.append(clip)
        else:
            entities.append(clip)

    newVersions.extend(scannerInstance._default_insertClips(binItem, non_entities))
    for component in entities:
        version = add_clip_as_version(component, binItem, scannerInstance._ftrack_component_reference)
        newVersions.append(version)

    scannerInstance._ftrack_component_reference = []
    return newVersions


