# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack_legacy as ftrack
import hiero

from nuke.assetmgr.nukestudiohost.hostAdaptor.NukeStudioHostAdaptor import utils

from ftrack_connect.ui.widget import overlay as _overlay
from ftrack_connect_nuke_studio.ui.tag_item import TagItem as _TagItem

import ftrack_connect_nuke_studio


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

    return utils.track.timingsFromTrackItem(item, opts)


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


def is_valid_tag_structure(tag_data):
    '''Return true if *tag_data* is valid.'''
    for track_item, context_tags in tag_data:
        if (
            not context_tags or
            not any([
                tag.metadata().value('ftrack.type') == 'show'
                for tag in context_tags
            ])
        ):
            return False, (
                'Project tag is missing from clip {0}. Use Tags to add '
                'context on clips.'
            ).format(track_item.name())

    return True, 'Success'


def tree_data_factory(tag_data_list):
    '''Return tree of TagItems out of a set of ftags om *tag_data_list*.'''
    processors = ftrack_connect_nuke_studio.processor.config()

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

        for hiero_tag in context:
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
