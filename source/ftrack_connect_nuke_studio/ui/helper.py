# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging
import math


import hiero
import ftrack_api

from ftrack_connect.session import get_shared_session


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

