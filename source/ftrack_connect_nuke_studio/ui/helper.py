# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging
import math

import ftrack
import hiero

import ftrack_connect_nuke_studio.exception
from ftrack_connect.ui.widget import overlay as _overlay
from ftrack_connect_nuke_studio.ui.tag_item import TagItem as _TagItem

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
        start += math.floor(trackItem.sourceIn())

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
    path = []

    parent = item.parent

    while parent:
        name = parent.name
        if name == 'root':
            parent = parent.parent
            continue
        path.append(parent.name)
        parent = parent.parent

    path.reverse()
    path.append(item.name)

    if not path:
        return False

    data = {'type': 'frompath', 'path': path}
    try:
        result = ftrack.xmlServer.action('get', data)
    except ftrack.api.ftrackerror.FTrackError:
        result = False

    return result


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


def validate_tag_structure(tag_data):
    '''Raise a ValidationError if tag structure is not valid.'''
    for track_item, context_tags in tag_data:
        if (not context_tags):
            message = (
                u'Context tags is missing from clip {0}. Use Tags to add '
                u'context on clips.'
            ).format(track_item.name())
            raise ftrack_connect_nuke_studio.exception.ValidationError(
                message
            )


def tree_data_factory(tag_data_list, project_tag):
    '''Return tree of TagItems out of a set of ftags om *tag_data_list*.'''

    # Define tag type sort orders.
    tag_sort_order = [
        'root',
        'show',
        'episode',
        'sequence',
        'shot',
        'task'
    ]

    # Create root node for the tree.
    root = {
        'ftrack.id': '0',
        'ftrack.type': 'root',
        'tag.value': 'root',
        'ftrack.name': 'ftrack'
    }

    # Create the root item.
    root_item = _TagItem(root)

    # Look into the tags and start creating the hierarchy.
    for trackItem, context in tag_data_list:

        # A clip entry, therefore the previous item is root.
        previous_item = root_item

        # Sort the tags, so we have them in the correct context order.
        def sort_context(x):
            if x.metadata().value('ftrack.type') in tag_sort_order:
                return tag_sort_order.index(x.metadata().value('ftrack.type'))

        context = sorted(context, key=lambda x: sort_context(x))

        for hiero_tag in [project_tag] + context:
            tag = _TagItem(hiero_tag.metadata().dict())
            tag.track = trackItem

            if tag.type not in tag_sort_order:
                # The given tag is not part of any known context.
                continue

            # Check if this tag already is children of the previous item and,
            # in case, re use it.
            if tag in previous_item.children:
                index = previous_item.children.index(tag)
                tag = previous_item.children[index]

            previous_item.addChild(tag)

            if tag.type == tag_sort_order[-1]:
                # We got to a leaf, use the parent as previous item.
                previous_item = tag.parent
            else:
                previous_item = tag

            tag.exists = item_exists(tag)

    return root_item
