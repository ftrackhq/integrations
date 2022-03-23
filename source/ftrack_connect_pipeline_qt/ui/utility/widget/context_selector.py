# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
import functools

from Qt import QtWidgets, QtCore

from ftrack_connect_pipeline import constants as constants
from ftrack_connect_pipeline.utils import get_current_context_id
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_info import EntityInfo
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser import (
    EntityBrowser,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import Context
from ftrack_connect_pipeline_qt.utils import BaseThread
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)


class ContextSelector(QtWidgets.QWidget):

    entityChanged = QtCore.Signal(object, object)

    @property
    def entity(self):
        return self._entity

    @property
    def context_id(self):
        return self._context_id

    def __init__(
        self,
        client,
        session,
        current_context_id=None,
        current_entity=None,
        parent=None,
    ):
        '''Initialise ContextSelector widget with the *current_entity* and
        *parent* widget.
        '''
        super(ContextSelector, self).__init__(parent=parent)
        self._entity = current_entity
        self._context_id = None
        self._current_context_id = current_context_id
        self.session = session
        self._client = client
        self._subscribe_id = None

        self.pre_build()
        self.build()
        self.post_build()

        self.set_default_context_id()
        self.set_entity(current_entity)

    def pre_build(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(10, 1, 10, 1)
        layout.setSpacing(8)
        self.setLayout(layout)

    def build(self):
        self.thumbnail_widget = Context(self.session)
        # self.thumbnail_widget.setScaledContents(True)

        self.thumbnail_widget.setMinimumWidth(50)
        self.thumbnail_widget.setMinimumHeight(50)
        self.thumbnail_widget.setMaximumWidth(50)
        self.thumbnail_widget.setMaximumHeight(50)

        if self._client.client_name == qt_constants.OPEN_WIDGET:
            self.entity_browser = EntityBrowser(
                self._client.get_parent_window(),
                self.session,
                title='CHOOSE TASK (WORKING CONTEXT)',
            )
            self.entity_browser.setMinimumWidth(600)
        else:
            self.entity_browser = None

        self.entity_info = EntityInfo()
        self.entity_info.setMinimumHeight(60)
        self.entity_info.setMaximumHeight(60)

        self.entity_browse_button = CircularButton(
            'edit', '#BF9AC9', variant='outlined'
        )

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
        self.setMaximumHeight(70)

    def host_changed(self, host_connection):
        '''Host has been set, listen to changes to context.'''
        if self._subscribe_id is not None:
            self.session.unsubscribe(self._subscribe_id)
            self._subscribe_id = None
        if self.entity_browser is None:  # Not do this for opener
            self._subscribe_id = self.session.event_hub.subscribe(
                'topic={} and data.pipeline.host_id={}'.format(
                    constants.PIPELINE_CONTEXT_CHANGE, host_connection.id
                ),
                self._global_context_changed,
            )

    def _global_context_changed(self, event):
        '''The main context has been set in another client (opener), align ourselves.'''
        context_id = event['data']['pipeline']['context_id']
        if self._context_id is None or context_id != self._context_id:
            context = self.find_context_entity(context_id)
            self._client.logger.info(
                'Aligning to new global context: {}({})'.format(
                    context['name'], context['id']
                )
            )
            self.set_entity(context, True)

    def set_default_context_id(self):
        '''Reset the context ID back to default.'''
        self.set_context_id(
            self._current_context_id or get_current_context_id()
        )

    def reset(self, entity=None):
        '''Reset browser to the given *entity* or the default one'''
        current_entity = entity or self._entity
        self.set_entity(current_entity)

    def set_entity(self, entity, global_context_change=False):
        '''Set the *entity* for the view.'''
        if not entity:
            return
        self._entity = entity
        self.entityChanged.emit(entity, global_context_change)
        self.entity_info.set_entity(entity)
        self._context_id = entity['id']

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
        # Ensure browser points to parent of currently selected entity.
        if self.entity_browser:
            self.entity_browser.set_entity(
                self._entity['parent'] if self._entity else None
            )
            # Launch browser.
            if self.entity_browser.exec_():
                self.set_entity(self.entity_browser.entity)
        else:
            if not self._client.is_docked():
                self._client.get_parent_window().hide()
                self._client.get_parent_window().destroy()
            self._client.host_connection.launch_widget(
                qt_constants.CHANGE_CONTEXT_WIDGET
            )
