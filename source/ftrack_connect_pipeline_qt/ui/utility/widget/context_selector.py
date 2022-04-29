# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
import logging

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

    changeContextClicked = QtCore.Signal()
    entityChanged = QtCore.Signal(object)

    @property
    def entity(self):
        return self._entity

    @property
    def context_id(self):
        return self._context_id

    def __init__(
        self,
        session,
        enble_entity_browser=False,
        parent=None,
    ):
        '''Initialise ContextSelector widget with the *current_entity* and
        *parent* widget. If *enble_entity_browser* is True, this contest selection is allowed to
        spawn the entity browser and change global context.
        '''
        super(ContextSelector, self).__init__(parent=parent)

        self.logger = logging.getLogger(__name__)

        self._enble_entity_browser = enble_entity_browser
        self._entity = None
        self._context_id = None
        self.session = session
        self._subscribe_id = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(10, 1, 10, 1)
        layout.setSpacing(8)
        self.setLayout(layout)
        if self._enble_entity_browser:
            self._entity_browser = EntityBrowser(
                self.parent(),
                self.session,
                title='CHOOSE TASK (WORKING CONTEXT)',
            )
            self._entity_browser.setMinimumWidth(600)

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
        self.thumbnail_widget.load(entity['id'])

    def post_build(self):
        self.entity_browse_button.clicked.connect(
            self._on_entity_browse_button_clicked
        )
        self.setMaximumHeight(50)

    def host_changed(self, host_connection):
        '''Host has been set, listen to context change (not opener)'''
        if self._subscribe_id is not None:
            self.session.unsubscribe(self._subscribe_id)
            self._subscribe_id = None
        self._subscribe_id = self.session.event_hub.subscribe(
            'topic={} and data.pipeline.host_id={}'.format(
                constants.PIPELINE_CONTEXT_CHANGE, host_connection.id
            ),
            self._ftrack_context_id_changed,
        )

    def _ftrack_context_id_changed(self, event):
        '''The main context has been set in another client (opener), align ourselves.'''
        context_id = event['data']['pipeline']['context_id']
        if self._context_id is None or context_id != self._context_id:
            context = self.find_context_entity(context_id)
            self.logger.info(
                'Aligning to new global context: {}({})'.format(
                    context['name'], context['id']
                )
            )
            self.set_entity(context)

    def reset(self, entity=None):
        '''Reset browser to the given *entity* or the default one'''
        current_entity = entity or self._entity
        self.set_entity(current_entity)

    def set_entity(self, entity):
        '''Set the *entity* for the view.'''
        if not entity:
            return
        do_emit_context_change = self._entity is not None
        self._entity = entity
        self.entity_info.set_entity(entity)
        self._context_id = entity['id']
        self.set_thumbnail(self._entity)
        if do_emit_context_change:
            self.entityChanged.emit(entity)

    def find_context_entity(self, context_id):
        context_entity = self.session.query(
            'select link, name , parent, parent.name from Context where id '
            'is "{}"'.format(context_id)
        ).one()
        return context_entity

    def set_context_id(self, context_id):
        if context_id:
            thread = BaseThread(
                name='context entity thread',
                target=self.find_context_entity,
                callback=self.set_entity,
                target_args=[context_id],
            )
            thread.start()

    def _on_entity_browse_button_clicked(self):
        '''Handle entity browse button clicked'''
        if self._enble_entity_browser:
            self._entity_browser.set_entity(
                self._entity['parent'] if self._entity else None
            )
            # Launch browser.
            if self._entity_browser.exec_():
                self.set_entity(self._entity_browser.entity)
        else:
            # Let client decide what to do when user wants to change context
            self.changeContextClicked.emit()
