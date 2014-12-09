# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import re
import hiero
from hiero.core.events import *
import FnAssetAPI.logging


class TagDropHandler(object):

    kTextMimeType = "text/plain"    
  
    def __init__(self):
        ''' Initialize the class and register the handler. 
        '''
        # hiero doesn't deal with drag and drop for text/plain data, so tell it to allow it
        hiero.ui.registerBinViewCustomMimeDataType(TagDropHandler.kTextMimeType)
        # register interest in the drop event now
        registerInterest((EventType.kDrop, EventType.kTimeline), self.dropHandler)

    def dropHandler(self, event):
        ''' Intercept the drop action on the timeline.

        Filter out any non ftrack tag, and uses the tag.re field to extract the context from the clip name,
        and set it back to the applied tag.
        '''
        currentTags = event.items

        for currentTag in currentTags:
            tag_name = currentTag.name()
            meta = currentTag.metadata()

            # Filter out any non ftrack tag
            if not meta.hasKey('type') or meta.value('type') != 'ftrack':
                FnAssetAPI.logging.debug('%s is not a valid track tag type' % tag_name)
                continue

            clip_name = event.trackItem.name()
            if tag_name == 'project':
                # print 'setting project to something'
                project = event.trackItem.project().name()
                FnAssetAPI.logging.debug('setting %s to %s on %s' % (tag_name, project, clip_name))
                meta.setValue('tag.value', project)

            # here we got a tag with a regular expression
            if meta.hasKey('tag.re'):
                match = meta.value('tag.re')
                if not match:
                    # somehow the tag.re is empty
                    continue

            result = re.match(match, clip_name)
            if result:
                result_value = result.groups()[-1]
                FnAssetAPI.logging.debug('setting %s to %s on %s' % (tag_name, result_value, clip_name))
                meta.setValue('tag.value', result_value)

    def unregister(self):
        ''' Unregister the handler.
        '''
        unregisterInterest((EventType.kDrop, EventType.kTimeline), self.dropHandler)
        hiero.ui.unregisterBinViewCustomMimeDataType(TagDropHandler.kTextMimeType)
