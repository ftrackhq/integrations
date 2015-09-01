# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import re
import logging

import hiero
from hiero.core.events import *


class TagDropHandler(object):

    kTextMimeType = "text/plain"

    def __init__(self):
        ''' Initialize the class and register the handler.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        # Nuke studio doesn't deal with drag and drop for text/plain data, so
        # tell it to allow it
        hiero.ui.registerBinViewCustomMimeDataType(
            TagDropHandler.kTextMimeType
        )

        # Register interest drop event.
        registerInterest(
            (EventType.kDrop, EventType.kTimeline), self.dropHandler
        )

    def dropHandler(self, event):
        ''' Intercept the drop *event* on the timeline.

        Filter out any non ftrack tag.

        '''
        currentTags = event.items

        for currentTag in currentTags:
            currentTag = currentTag.copy()
            current_item = event.trackItem
            tag_name = currentTag.name()
            meta = currentTag.metadata()

            # Filter out any non ftrack tag
            if not meta.hasKey('type') or meta.value('type') != 'ftrack':
                self.logger.debug(
                    '{0} is not a valid track tag type'.format(tag_name)
                )
                continue

            if not isinstance(current_item, hiero.core.TrackItem):
                continue

            current_item.addTag(currentTag)
            event.dropEvent.accept()

    def unregister(self):
        ''' Unregister the handler.'''
        unregisterInterest(
            (EventType.kDrop, EventType.kTimeline), self.dropHandler
        )

        hiero.ui.unregisterBinViewCustomMimeDataType(
            TagDropHandler.kTextMimeType
        )
