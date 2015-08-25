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

        Filter out any non ftrack tag, and uses the tag.re field to extract
        the context from the clip name, and set it back to the applied tag.

        '''
        currentTags = event.items

        for currentTag in currentTags:
            currentTag = currentTag.copy()
            current_item = event.trackItem
            tag_name = currentTag.name()
            meta = currentTag.metadata()

            # Filter out any non ftrack tag
            if not meta.hasKey('type') or meta.value('type') != 'ftrack':
                logging.debug(
                    '{0} is not a valid track tag type'.format(tag_name)
                )
                continue

            clip_name = event.trackItem.name()
            if tag_name == 'project':
                # Skip project tags since it's added by the create project
                # dialog.
                logging.debug(
                    '{0} is not a valid track tag type'.format(tag_name)
                )

                # Accept the event to prevent further processing of the
                # the dropped tags.
                event.dropEvent.accept()
                continue

            # Handle a tag with a regular expression.
            elif meta.hasKey('tag.re'):
                match = meta.value('tag.re')
                if not match:
                    # If the regular expression is empty skip it.
                    continue

                result = re.match(match, clip_name)
                if result:
                    result_value = result.groups()[-1]
                    logging.debug(
                        'Setting {0} to {1} on {2}'.format(
                            tag_name, result_value, clip_name
                        )
                    )
                    meta.setValue('tag.value', result_value)

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
