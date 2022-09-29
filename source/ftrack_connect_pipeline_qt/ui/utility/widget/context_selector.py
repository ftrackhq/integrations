# :coding: utf-8
# :copyright: Copyright (c) 2015-2022 ftrack
import logging
import shiboken2

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline import constants as constants
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_info import EntityInfo

from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import Context
from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser import (
    EntityBrowser,
)


class ContextSelector(QtWidgets.QFrame):
    '''Widget representing the current context by showing entity info, and a button enabling change of context'''

    changeContextClicked = QtCore.Signal()
    entityChanged = QtCore.Signal(object)
    entityFound = QtCore.Signal(object)

    @property
    def entity(self):
        '''Return the entity'''
        return self._entity

    @entity.setter
    def entity(self, value):
        '''Set the entity to *value*'''
        if not value:
            return
        do_emit_context_change = self._entity is not None
        self._entity = value
        self.entity_info.entity = value
        self._context_id = value['id']
        self.set_thumbnail(self._entity)
        if do_emit_context_change:
            self.entityChanged.emit(value)

    @property
    def context_id(self):
        '''Return the context id'''
        return self._context_id

    @context_id.setter
    def context_id(self, value):
        '''Set the entity context id to *value*'''
        if not value:
            return
        thread = BaseThread(
            name='find-context-entity-thread',
            target=self._find_context_entity,
            callback=self._on_entity_found_async,
            target_args=[value],
        )
        thread.start()

    def __init__(
        self,
        session,
        enble_context_change=False,
        parent=None,
    ):
        '''
        Initialise ContextSelector widget

        :param session: :class:`ftrack_api.session.Session`
        :param enble_context_change:  If set to to True, this contest selection is allowed to spawn the entity browser and change global context.
        :param parent: The parent dialog or frame
        '''

        super(ContextSelector, self).__init__(parent=parent)

        self.logger = logging.getLogger(__name__)

        self._enble_context_change = enble_context_change
        self._entity = None
        self._context_id = None
        self.session = session

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(10, 1, 10, 1)
        layout.setSpacing(8)
        self.setLayout(layout)

    def build(self):
        self.thumbnail_widget = Context(self.session)

        self.thumbnail_widget.setMinimumWidth(50)
        self.thumbnail_widget.setMinimumHeight(40)
        self.thumbnail_widget.setMaximumWidth(50)
        self.thumbnail_widget.setMaximumHeight(40)

        self.entity_info = EntityInfo()
        self.entity_info.setMinimumHeight(40)
        self.entity_info.setMaximumHeight(40)

        self.entity_browse_button = CircularButton('edit', variant='outlined')

        self.layout().addWidget(self.thumbnail_widget)
        self.layout().addWidget(self.entity_info)
        self.layout().addWidget(QtWidgets.QLabel(), 10)
        self.layout().addWidget(self.entity_browse_button)

    def set_thumbnail(self, entity):
        '''Set the entity thumbnail'''
        self.thumbnail_widget.load(entity['id'])

    def post_build(self):
        self.entity_browse_button.clicked.connect(
            self._on_entity_browse_button_clicked
        )
        self.entityFound.connect(self._on_entity_found)
        self.setMaximumHeight(50)

    def _ftrack_context_id_changed(self, event):
        '''The main context has been set in another client (opener), align ourselves.'''
        context_id = event['data']['pipeline']['context_id']
        if self._context_id is None or context_id != self._context_id:
            context = self._find_context_entity(context_id)
            self.logger.info(
                'Aligning to new global context: {}({})'.format(
                    context['name'], context['id']
                )
            )
            self.entity = context

    def reset(self, entity=None):
        '''Reset browser to the given *entity* or the default one'''
        current_entity = entity or self._entity
        self.entity = current_entity

    def _find_context_entity(self, context_id):
        '''(Run in background thread) Query entity from ftrack'''
        context_entity = self.session.query(
            'select link, name , parent, parent.name from Context where id '
            'is "{}"'.format(context_id)
        ).one()
        return context_entity

    def _on_entity_found_async(self, entity):
        '''(Run in background thread) Entity found callback'''
        if not shiboken2.isValid(self):
            # Widget has been closed while entity fetched
            return
        self.entityFound.emit(entity)

    def _on_entity_found(self, entity):
        '''Entity found callback, set entity'''
        self.entity = entity

    def _on_entity_browse_button_clicked(self):
        '''Handle entity browse button clicked'''

        if self._enble_context_change:
            entity_browser = EntityBrowser(
                self.parent(),
                self.session,
                title='CHOOSE TASK (WORKING CONTEXT)',
            )
            entity_browser.setMinimumWidth(600)
            entity_browser.entity = (
                self._entity['parent'] if self._entity else None
            )
            # Launch browser.
            if entity_browser.exec_():
                self.entity = entity_browser.entity
        else:
            # Let client decide what to do when user wants to change context
            self.changeContextClicked.emit()
