# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import logging

from Qt import QtGui

import hiero
from hiero.core.VersionScanner import VersionScanner
from ftrack_connect_nuke_studio.session import get_shared_session
from ftrack_connect_nuke_studio.base import FtrackBase

session = get_shared_session()
logger = logging.getLogger(__name__)

current_ftrack_location = session.pick_location()
Base = FtrackBase()
hiero_version_tuple = Base.hiero_version_tuple


def register_versioning_overrides():
    ''' Register overrides for VersionScanner object. '''
    logger.debug('register_versioning_overrides')

    # We want to redefine some of the methods of VersionScanner,
    # but may still need to use the default functionality within our custom methods.
    # Therefore, we need to save a reference to the default methods, and then we will be able to call them from ours.
    if not hasattr(VersionScanner, '_default_findVersionFiles'):
        VersionScanner._default_findVersionFiles = VersionScanner.findVersionFiles
        VersionScanner.findVersionFiles = ftrack_find_version_files

    if not hasattr(VersionScanner, '_default_filterVersion'):
        VersionScanner._default_filterVersion = VersionScanner.filterVersion
        VersionScanner.filterVersion = ftrack_filter_version

    # Conditional depending on nuke studio / hiero version
    if hiero_version_tuple < (11, 3, 0):
        # < 11.3vX
        if not hasattr(VersionScanner, '_default_insertClips'):
            VersionScanner._default_insertClips = VersionScanner.insertClips
            VersionScanner.insertClips = ftrack_insert_clips

        if not hasattr(VersionScanner, '_default_createClip'):
            VersionScanner._default_createClip = VersionScanner.createClip
            VersionScanner.createClip = ftrack_create_clip
    else:
        # > 11.2vX
        if not hasattr(VersionScanner, '_default_createAndInsertClipVersion'):
            VersionScanner._default_createAndInsertClipVersion = VersionScanner.createAndInsertClipVersion
            VersionScanner.createAndInsertClipVersion = ftrack_create_and_insert_clip_version

    VersionScanner._ftrack_component_reference = []
    hiero.core.events.registerInterest('kShowContextMenu/kTimeline', customise_menu)


def customise_menu(event):
    ''' Set ftrack icon looking in menu from given *event*. '''
    actions = event.menu.actions()
    for action in actions:
        if action.text() in ['Version', 'Export...']:
            action.setIcon(QtGui.QPixmap(':ftrack/image/default/ftrackLogoLight'))


def add_ftrack_build_tag(clip, component):
    ''' Add custom ftrack tag and enforce *clip* name from *component*. '''
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
    '''Return ftrack tag if present in given *clip*. '''
    existing_tag = None
    for tag in clip.tags():
        if tag.metadata().hasKey('tag.provider') and tag.metadata()['tag.provider'] == 'ftrack':
            existing_tag = tag
            break

    if not existing_tag:
        return False
    return existing_tag


def add_clip_as_version(clip, bin_item, ftrack_component_reference):
    ''' Return a new version from *clip* correctly inserted in *bin_item* through *ftrack_component_reference* lookup. '''
    has_tag = get_ftrack_tag(clip)
    component_id = has_tag.metadata()['component_id']
    component = session.get('Component', component_id)
    version_index = ftrack_component_reference.index(component)
    target_bin_index = -1

    bin_index = 0
    for version in bin_item.items():
        bin_clip = version.item()
        bin_clip_has_tag = get_ftrack_tag(bin_clip)
        bin_clip_component_id = bin_clip_has_tag.metadata()['component_id']
        bin_clip_component = session.get('Component', bin_clip_component_id)
        bin_clip_index = ftrack_component_reference.index(bin_clip_component)
        set_version_index = bin_clip_index >= version_index
        try:
            if set_version_index:
                target_bin_index = bin_index
                break
        except:
            pass
        bin_index += 1

    version = hiero.core.Version(clip)
    bin_item.addVersion(version, target_bin_index)
    return version


# Overrides
def ftrack_find_version_files(scanner_instance, version):
    ''' Return paths for given *version*. '''
    clip = version.item()
    ftrack_tag = get_ftrack_tag(clip)

    if not ftrack_tag:
        return scanner_instance._default_findVersionFiles(version)

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

    scanner_instance._ftrack_component_reference = []

    for component in sorted_components:
        component_avaialble = session.pick_location(component)
        if component_avaialble:
            scanner_instance._ftrack_component_reference.append(component)

    hiero_ordered_versions = scanner_instance._ftrack_component_reference[::-1]

    # Prune out any we already have
    binitem = version.parent()
    filtered_paths = filter(lambda v : scanner_instance.filterVersion(binitem, v), hiero_ordered_versions)
    return filtered_paths


def ftrack_filter_version(scanner_instance, bin_item, new_version_file):
    ''' Return whether the given *new_version_file* already exist in *bin_item*. '''
    # We have to see if anything else in the bin has this ref
    bin_ftrack_tag = get_ftrack_tag(bin_item.items()[0].item()) # let's check if the first version has it...
    if not bin_ftrack_tag:
        return scanner_instance._default_filterVersion(bin_item, new_version_file)

    for version in bin_item.items():
        item = version.item()
        ftrack_tag = get_ftrack_tag(item)
        if ftrack_tag:
            component_id = ftrack_tag.metadata()['component_id']
            if (
                  component_id == new_version_file['id']
            ):
                return False

    return True


def ftrack_create_clip(scanner_instance, new_filename):
    ''' Return a new clip from *new_filename* through lookup. '''
    if new_filename in scanner_instance._ftrack_component_reference:
        is_available = session.pick_location(new_filename)
        if not is_available:
            return

        file_path = current_ftrack_location.get_filesystem_path(new_filename).split()[0]
        clip = hiero.core.Clip(file_path)
        add_ftrack_build_tag(clip, new_filename)
        return clip
    else:
        return scanner_instance._default_createClip(new_filename)


def ftrack_insert_clips(scanner_instance, bin_item, clips):
    ''' Return versions created in *bin_item* from *clips*. '''
    entities = []
    non_entities = []
    new_versions = []

    for clip in clips:
        has_tags = get_ftrack_tag(clip)
        if not has_tags:
            non_entities.append(clip)
        else:
            entities.append(clip)

    new_versions.extend(scanner_instance._default_insertClips(bin_item, non_entities))
    for component in entities:
        version = add_clip_as_version(component, bin_item, scanner_instance._ftrack_component_reference)
        new_versions.append(version)

    scanner_instance._ftrack_component_reference = []
    return new_versions

# NS >= 11.3vX
def ftrack_create_and_insert_clip_version(scanner_instance, bin_item, new_filename):
    if new_filename not in scanner_instance._ftrack_component_reference:
        return scanner_instance._default_createAndInsertClipVersion(bin_item, new_filename)

    clip = ftrack_create_clip(scanner_instance, new_filename)
    version = add_clip_as_version(clip, bin_item, scanner_instance._ftrack_component_reference)

    return version
