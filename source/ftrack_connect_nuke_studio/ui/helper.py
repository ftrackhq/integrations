# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import ftrack
from ftrack_connect.ui.widget import overlay as _overlay
from ftrack_connect_nuke_studio.ui.tag_item import TagItem as _TagItem
import ftrack_connect_nuke_studio
import assetmgr_hiero

import hiero


def sourceFromTrackItem(item):
    ''' Extract the source material from the give nuke studio's trackItem.
    '''
    clip = item.source()
    media = clip.mediaSource()
    file_info = media.fileinfos()[0]
    file_path = file_info.filename()
    return file_path


def timecodeFromTrackItem(item):
    ''' Extract timecode infomrations from the given nuke studio's trackItem.
    '''
    sourceTimecodeIn = item.source().timecodeStart() + item.sourceIn()
    sourceTimecodeOut = item.source().timecodeStart() + item.sourceOut()

    destinationTimecodeIn = item.parentSequence().timecodeStart() + item.timelineIn()
    destinationTimecodeOut = item.parentSequence().timecodeStart() + item.timelineOut()

    framerate = item.parentSequence().framerate()
    _in_src = hiero.core.Timecode.timeToString(sourceTimecodeIn, framerate, hiero.core.Timecode.kDisplayTimecode, False)
    _out_src = hiero.core.Timecode.timeToString(sourceTimecodeOut, framerate, hiero.core.Timecode.kDisplayTimecode, False)

    _in_dst = hiero.core.Timecode.timeToString(destinationTimecodeIn, framerate, hiero.core.Timecode.kDisplayTimecode, False)
    _out_dst = hiero.core.Timecode.timeToString(destinationTimecodeOut, framerate, hiero.core.Timecode.kDisplayTimecode, False)

    return _in_src, _out_src, _in_dst, _out_dst


def timeFromTrackItem(item, parent):
    ''' Extract time infomrations from the given nuke studio's trackItem.
    '''
    hadles = parent.spinBox_handles.value()
    frames = parent.spinBox_offset.value()

    opts = {
        'numbering' : ('custom' ), # custom
        'customNumberingStart' : frames,
        'handles' : ('custom' ), # custom
        'customHandleLength' : hadles,
        'includeRetiming' : True,
        'clampToPositive' : True
    }

    return assetmgr_hiero.utils.track.timingsFromTrackItem(item, opts)


def itemExists(item):
    ''' Check if the given item exists on the server already
    '''

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

    data = {'type':'frompath','path':path}
    try:
        result = ftrack.xmlServer.action('get',data)
    except ftrack.api.ftrackerror.FTrackError:
        result = False

    return result



class TagTreeOverlay(_overlay.BusyOverlay):
    '''custom reimplementation for style purposes'''
    def __init__(self, parent=None):
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
                border-image: url(:ftrack/image/default/boxShadow) 140 stretch;
            }

            BlockingOverlay QLabel {
                background: transparent;
            }
        ''')


def treeDataFactory(tagDataList):
    ''' Build a tree of TagItem out of a set of ftags.
    '''

    processors = ftrack_connect_nuke_studio.processor.config()

    # Define tag type sort orders
    tag_sort_order = [
        'root',
        'show',
        'episode',
        'sequence',
        'shot',
        'task',
        # 'asset',
        # 'assetVersion',
        # 'component'
    ]

    # Create root node for the tree
    root = {
        'ftrack.id':'0',
        'ftrack.type':'root',
        'tag.value': 'root',
        'ftrack.name': 'ftrack'
    }

    # Create the root item
    root_item = _TagItem(root)

    # Look into the tags and start creating the hierarchy
    for trackItem, context in tagDataList:

        # A clip entry, therefore the previous item is root
        previous_item = root_item

        # Sort the tags, so we have them in the correct context order
        def sort_context(x):
            if x.metadata().value('ftrack.type') in tag_sort_order:
                return tag_sort_order.index(x.metadata().value('ftrack.type'))

        context = sorted(context, key=lambda x : sort_context(x))

        for hiero_tag in context:

            tag = _TagItem(hiero_tag.metadata().dict())
            tag.track = trackItem

            if tag.type not in tag_sort_order:
                # The given tag is not part of any known context
                continue

            # Check if this tag already is children of the previous item and, in case, re use it.
            if tag in previous_item.children:
                index = previous_item.children.index(tag)
                tag = previous_item.children[index]

            previous_item.addChild(tag)

            if tag.type == tag_sort_order[-1]:
                # We got to a leaf, use the parent as previous item.
                previous_item = tag.parent
            else:
                previous_item = tag

            tag.exists = itemExists(tag)

    return root_item
