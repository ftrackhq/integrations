# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging
import math


import hiero
import ftrack_api

import ftrack_connect_nuke_studio.exception
import ftrack_connect_nuke_studio.template

from ftrack_connect.session import get_shared_session
from ftrack_connect.ui.widget import overlay as _overlay
from ftrack_connect_nuke_studio.ui.tree_item import TreeItem as _TreeItem


session = get_shared_session()

kTimingOption_numbering = 'numbering'
kTimingOption_customNumberingStart = 'customNumberingStart'
kTimingOption_handles = 'handles'
kTimingOption_customHandleLength = 'customHandleLength'
kTimingOption_includeRetiming = 'includeRetiming'
kTimingOption_clampToPositive = 'clampToPositive'
kTimingOption_includeSourceTimecode = 'includeSourceTimecode'
kTimingOption_includeInTimecode = 'includeInTimecode'

kTimingOptions_numbering = ('clip', 'custom')
kTimingOptions_handles = ('none', 'custom', 'clip', 'customClip')

kTimingOptionDefaults = {
    kTimingOption_numbering : 'clip',
    kTimingOption_customNumberingStart : 1001,
    kTimingOption_handles : 'none',
    kTimingOption_customHandleLength : 12,
    kTimingOption_clampToPositive : True,
    kTimingOption_includeRetiming : True,
    kTimingOption_includeInTimecode : False,
    kTimingOption_includeSourceTimecode : False
}

def timings_from_track_item(track_item, options):
    '''Copy from nuke studio assetmgr.

    @param opts Options to control how timings are extracted
    opts = {
        'numbering' : ( 'clip', 'custom' ), # clip
        'customNumberingStart' : 1001,
        'handles' : ( 'none', 'custom', 'clip', 'customClip' ), # none
        'customHandleLength' : 12,
        'includeRetiming' : True,
        'clampToPositive' : True
    }
    '''

    # Ensure we have some sensible, known defaults
    opts = dict(kTimingOptionDefaults)
    opts.update(options)

    start = end = in_ = out = 0

    clip = track_item.source()
    if not clip:
        logging.debug((
            'No clip available for {0} - clip based timings '
            'will be ignored'
        ).format(track_item))

    numbering = opts[kTimingOption_numbering]
    if numbering == 'custom':
        # If we're using a custom start frame, override the clip's start frame number
        start = opts[kTimingOption_customNumberingStart]
    elif numbering == 'clip' and clip:
        # If we have a clip, use its frame numbers
        start = clip.timelineOffset()
        # Make sure we factor in the in point of the TrackItem, its relative
        # The floor is to account for re-times
        start += math.floor(track_item.sourceIn())

    handles = opts[kTimingOption_handles]
    try:
        customHandleLength = int(opts[kTimingOption_customHandleLength])
    except ValueError:
        pass

    editLength = track_item.timelineOut() - track_item.timelineIn()
    if opts[kTimingOption_includeRetiming]:
        # If its a single frame clip then don't include retiming, as it'll be '0',
        # which though correct, isnt helpfull here.
        if clip.duration() != 1:
            editLength = math.ceil(editLength * track_item.playbackSpeed())


    # We want to anchor the 'in' point to the chosen starting frame number, and
    # subtract handles as necessary rather than shifting the edit start frame.
    # Start off with no handles.
    in_ = start

    # The 'length' of the shot is always the edit length of the track item
    out = in_ + editLength

    # No handles on the end either to start with
    end = out

    # Apply handles based on clip length (floor to take into account retimes)
    if handles in ('clip', 'customClip') and clip:
        start -= math.floor(track_item.sourceIn())
        end = start + clip.duration()

    # Add any custom handles
    if handles in ('custom', 'customClip'):
        start -= customHandleLength
        end += customHandleLength

    # Ensure we don't go out of range if we're asked to clamp
    if opts[kTimingOption_clampToPositive]:
        start = max(0, start)
        in_ = max(0, in_)
        out = max(0, out)
        end = max(0, end)

    return start, end, in_, out


def source_from_track_item(item):
    '''Return source material from nuke studio's trackItem *item*.'''
    clip = item.source()
    media = clip.mediaSource()
    file_info = media.fileinfos()[0]
    file_path = file_info.filename()
    return file_path


def timecode_from_track_item(item):
    '''Return timecode information nuke studio's trackItem *item*.'''
    sourceTimecodeIn = item.source().timecodeStart() + item.sourceIn()
    sourceTimecodeOut = item.source().timecodeStart() + item.sourceOut()

    destinationTimecodeIn = item.parentSequence(
    ).timecodeStart() + item.timelineIn()
    destinationTimecodeOut = item.parentSequence(
    ).timecodeStart() + item.timelineOut()

    framerate = item.parentSequence().framerate()
    _in_src = hiero.core.Timecode.timeToString(
        sourceTimecodeIn, framerate, hiero.core.Timecode.kDisplayTimecode, False)
    _out_src = hiero.core.Timecode.timeToString(
        sourceTimecodeOut, framerate, hiero.core.Timecode.kDisplayTimecode, False)

    _in_dst = hiero.core.Timecode.timeToString(
        destinationTimecodeIn, framerate, hiero.core.Timecode.kDisplayTimecode, False)
    _out_dst = hiero.core.Timecode.timeToString(
        destinationTimecodeOut, framerate, hiero.core.Timecode.kDisplayTimecode, False)

    return _in_src, _out_src, _in_dst, _out_dst


def time_from_track_item(item, parent):
    '''Return time information nuke studio's trackItem *item*.'''
    handles = parent.handles_spinbox.value()
    frames = parent.start_frame_offset_spinbox.value()

    opts = {
        'numbering': ('custom'),  # custom
        'customNumberingStart': frames,
        'handles': ('custom'),  # custom
        'customHandleLength': handles,
        'includeRetiming': True,
        'clampToPositive': True
    }

    return timings_from_track_item(item, opts)


def item_exists(item):
    '''Return entity if *item* exists on the server, otherwise false.'''
    path = [item.name]

    parent = item.parent

    while parent:
        name = parent.name
        if name == 'root':
            parent = parent.parent
            continue
        path.append(parent.name)
        parent = parent.parent

    if not path:
        return False

    try:
        query = [u'select id from Context where name = "{0}"'.format(
                path[0]
            )
        ]

        for level, part in enumerate(path[1:]):
            query.append(
                u'{0}.name = "{1}"'.format(
                    '.'.join(['parent'] * (level + 1)), part
                )
            )

        return session.query(
            u' and '.join(query)
        ).one()

    except (ftrack_api.exception.MultipleResultsFoundError,
            ftrack_api.exception.NoResultFoundError):

            return False

    return True


#: TODO: Remove this when styling is in a separate file.
class TagTreeOverlay(_overlay.BusyOverlay):
    '''Custom reimplementation for style purposes'''

    def __init__(self, parent=None):
        '''Initiate and set style sheet.'''
        super(TagTreeOverlay, self).__init__(parent=parent)

        self.setStyleSheet('''
            BlockingOverlay {
                background-color: rgba(58, 58, 58, 200);
                border: none;
            }

            BlockingOverlay QFrame#content {
                padding: 0px;
                border: 80px solid transparent;
                background-color: transparent;
                border-image: none;
            }

            BlockingOverlay QLabel {
                background: transparent;
            }
        ''')


def tree_data_factory(track_item_data, project_tag, template):
    '''Return tree of TreeItems out of a set of track items in *track_item_data*.

    *project_tag* should be a `hiero.core.Tag` with metadata referring to
    the project in ftrack.

    *template* should be a context template.

    '''
    # Create root node for the tree.
    root = {
        'ftrack.id': '0',
        'ftrack.type': 'root',
        'tag.value': 'root',
        'ftrack.name': 'ftrack'
    }

    # Create the root item.
    root_item = _TreeItem(root)

    project_name = project_tag.metadata().value('tag.value')
    project_item = _TreeItem({
        'name': project_name,
        'ftrack.id': None,
        'ftrack.type': 'show',
        'ftrack.name': project_name,
        'tag.value': project_name
    })
    project_item.exists = item_exists(project_item)

    not_matching_item = _TreeItem({
        'name': project_name,
        'ftrack.id': 'not_matching_template',
        'ftrack.type': 'report',
        'ftrack.name': 'clips not matching the selected template',
        'tag.value': 'clips not matching the selected template'
    })

    not_matching_item.exists = 'error'
    root_item.addChild(project_item)

    for track_item, task_types in track_item_data:

        # A new track item, therefore the previous item is the project.
        previous_item = project_item

        try:
            contexts = ftrack_connect_nuke_studio.template.match(
                track_item, template
            )
        except ftrack_connect_nuke_studio.exception.TemplateError:
            # The track item did not match the selected template.
            item = _TreeItem({
                'name': project_name,
                'ftrack.id': None,
                'ftrack.type': 'close',
                'ftrack.name': track_item.name(),
                'tag.value': track_item.name(),
                'existing': False
            })

            item.exists = 'error'
            not_matching_item.addChild(item)

        else:
            # First generate the structure for contexts matching the given
            # template.
            for entity in contexts:
                item = _TreeItem({
                    'name': entity['name'],
                    'ftrack.id': None,
                    'ftrack.type': entity['object_type'].lower(),
                    'ftrack.name': entity['name'],
                    'tag.value': entity['name']
                })

                item.track = track_item

                if item in previous_item.children:
                    index = previous_item.children.index(item)
                    item = previous_item.children[index]

                previous_item.addChild(item)

                previous_item = item
                item.exists = item_exists(item)

            # Generate tasks based on the task type tags on the track item.
            for task_type in task_types:
                metadata = task_type.metadata().dict()

                # Skip any tag not of task type.
                if metadata.get('ftrack.type') != 'task':
                    continue

                item = _TreeItem(metadata)
                item.track = track_item

                previous_item.addChild(item)
                item.exists = item_exists(item)

    if not_matching_item.children:
        root_item.addChild(not_matching_item)

    return root_item
