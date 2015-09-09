# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import logging

import hiero
import hiero.core.events


class TagDropHandler(object):

    kTextMimeType = "text/plain"

    def __init__(self):
        '''Initialize the class and register the handler.'''
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        # Nuke studio doesn't deal with drag and drop for text/plain data, so
        # tell it to allow it
        hiero.ui.registerBinViewCustomMimeDataType(
            TagDropHandler.kTextMimeType
        )

        # Register interest drop event.
        hiero.core.events.registerInterest(
            (
                hiero.core.events.EventType.kDrop,
                hiero.core.events.EventType.kTimeline
            ),
            self.dropHandler
        )

    def dropHandler(self, event):
        '''Intercept the drop *event* on the timeline.

        Filter out any non ftrack tag.

        '''
        try:
            track_item = event.trackItem
        except AttributeError:
            return

        dropped_tags = event.items
        existing_ftrack_tag_names = []

        # Create a list of ftrack tags on the target track item. This is used to
        # filter out duplicates.
        for existing_tag in track_item.tags():
            meta = existing_tag.metadata()
            if meta.hasKey('type') and meta.value('type') == 'ftrack':
                existing_ftrack_tag_names.append(
                    existing_tag.name()
                )

        self.logger.debug(
            'Existing ftrack tags names: {0}'.format(existing_ftrack_tag_names)
        )

        for tag in dropped_tags:
            tag = tag.copy()
            tag_name = tag.name()
            meta = tag.metadata()

            # Skip adding tag if it already exists on the track item.
            if tag_name in existing_ftrack_tag_names:
                self.logger.debug(
                    '{0} already exists on {1}'.format(tag_name, track_item)
                )
                event.dropEvent.accept()
                continue

            # Filter out any non ftrack tags.
            if not meta.hasKey('type') or meta.value('type') != 'ftrack':
                self.logger.debug(
                    '{0} is not a valid track tag type'.format(tag_name)
                )
                continue

            if (
                not meta.hasKey('ftrack.id')
                or meta.value('ftrack.id') == 'show'
            ):
                self.logger.debug(
                    '{0} is not a valid track tag type'.format(tag_name)
                )
                event.dropEvent.accept()
                continue

            track_item.addTag(tag)
            event.dropEvent.accept()

    def unregister(self):
        '''Unregister the handler.'''
        hiero.core.events.unregisterInterest(
            (
                hiero.core.events.EventType.kDrop,
                hiero.core.events.EventType.kTimeline
            ),
            self.dropHandler
        )

        hiero.ui.unregisterBinViewCustomMimeDataType(
            TagDropHandler.kTextMimeType
        )
