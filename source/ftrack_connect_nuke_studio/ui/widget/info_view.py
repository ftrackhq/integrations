# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import urlparse

import hiero.core
import ftrack_connect.ui.widget.web_view

import logging

import ftrack_connect_nuke_studio.entity_reference

from ftrack_connect.session import (
    get_shared_session
)

session = get_shared_session()

class InfoView(
    ftrack_connect.ui.widget.web_view.WebView
):
    '''Display information about selected entity.'''

    _identifier = 'com.ftrack.information_panel'
    _display_name = 'Info'

    def __init__(self, parent=None, url=None):
        '''Initialise InvfoView.'''
        super(InfoView, self).__init__(parent, url)

        hiero.core.events.registerInterest(
            'kSelectionChanged', self.on_selection_changed
        )

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        self.setWindowTitle(self._display_name)
        self.setObjectName(self._identifier)

    @classmethod
    def get_identifier(self):
        '''Return identifier for widget.'''
        return self._identifier

    @classmethod
    def get_display_name(self):
        '''Return dsiplay name for widget.'''
        return self._display_name

    def set_entity(self, entity):
        '''Display information about specific *entity*.'''
        if entity is None:
            return

        if entity.entity_type is 'Component':
            entity = entity.get('version')

        if not self.get_url():
            url = session.get_widget_url(
                'info', entity=entity, theme='tf'
            )

            # Load initial page using url retrieved from entity.
            self.set_url(
                url
            )

        else:
            # Send javascript to currently loaded page to update view.
            entityId = entity.get('id')

            entityType = ftrack_connect_nuke_studio.entity_reference.translate_to_legacy_entity_type(
                entity.entity_type
            )


            javascript = (
                'FT.WebMediator.setEntity({{'
                '   entityId: "{0}",'
                '   entityType: "{1}"'
                '}})'
                .format(entityId, entityType)
            )
            self.evaluateJavaScript(javascript)

    def on_selection_changed(self, event):
        '''Handle selection changed events.'''
        selection = event.sender.selection()

        selection = [
            _item for _item in selection
            if isinstance(_item, hiero.core.TrackItem)
        ]

        if len(selection) != 1:
            return

        item = selection[0]
        entity = ftrack_connect_nuke_studio.entity_reference.get(
            item
        )

        if not entity:
            return

        self.set_entity(entity)