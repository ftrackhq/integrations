# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import shiboken2

from Qt import QtWidgets, QtCore

from ftrack_qt.widgets.info import EntityInfo

from ftrack_qt.widgets.thumbnails import ContextThumbnail
from ftrack_utils.threading import BaseThread
from ftrack_qt.widgets.buttons import CircularButton

# TODO: this code has to be reviewed


class ContextSelector(QtWidgets.QFrame):
    '''Widget representing the current context by showing entity info, and a button enabling change of context'''

    change_context_clicked = QtCore.Signal()
    entity_changed = QtCore.Signal(object)
    context_changed = QtCore.Signal(object)
    entity_found = QtCore.Signal(object)
    disable_thumbnail = False

    @property
    def entity(self):
        '''Return the entity'''
        return self._entity

    @entity.setter
    def entity(self, value):
        '''Set the entity to *value*'''
        # prevent setting the same entity twice
        if value == self._entity:
            return
        self._entity = value
        self.entity_info.entity = value
        self._context_id = value['id'] if value else None
        if not self.disable_thumbnail:
            self.set_thumbnail(self._entity)
        self.entity_changed.emit(value)
        self.context_changed.emit(value['id'])
        self.entity_info.setVisible(self.entity is not None)
        self.no_entity_label.setVisible(self.entity is None)

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
        self.__thread_registry.append(thread)
        self._browsing_context = True
        thread.start()

    @property
    def is_browsing(self):
        browsing = False
        for thread in self.__thread_registry:
            if thread.is_alive() or self._browsing_context:
                browsing = True
                break
        return browsing

    @property
    def browse_context_id(self):
        '''Return the browse context id'''
        return self._browse_context_id

    @browse_context_id.setter
    def browse_context_id(self, value):
        '''Set the initial browse context id'''
        self._browse_context_id = value

    @property
    def entity_browser(self):
        '''Return the entity browser'''
        return self._entity_browser

    def __init__(
        self,
        session,
        enable_context_change=False,
        select_task=True,
        browse_context_id=None,
        parent=None,
    ):
        '''
        Initialise ContextSelector widget

        :param session: :class:`ftrack_api.session.Session`
        :param enable_context_change:  If set to True, this contest selection is allowed to spawn the entity browser
            and change global context.
        :param select_task: If true. only tasks can be selected in the entity browser. If false, any context can be selected.
        :param browse_context_id: If set, the entity browser will be opened with this context id as the root.
        :param parent: The parent dialog or frame
        '''

        super(ContextSelector, self).__init__(parent=parent)

        self.logger = logging.getLogger(__name__)

        self._enable_context_change = enable_context_change
        self._select_task = select_task
        self._browse_context_id = browse_context_id
        self._entity = None
        self._context_id = None
        self.session = session
        self.__thread_registry = []
        self._browsing_context = False
        self._entity_browser = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(10, 1, 10, 1)
        layout.setSpacing(8)
        self.setLayout(layout)

    def build(self):
        from ftrack_qt.widgets.browsers import (
            EntityBrowser,
        )  # Prevent circular import

        self.thumbnail_widget = ContextThumbnail(self.session)

        self.thumbnail_widget.setMinimumWidth(50)
        self.thumbnail_widget.setMinimumHeight(40)
        self.thumbnail_widget.setMaximumWidth(50)
        self.thumbnail_widget.setMaximumHeight(40)

        self.entity_info = EntityInfo()
        self.entity_info.setMinimumHeight(40)
        self.entity_info.setMaximumHeight(40)
        self.entity_info.setVisible(False)

        self.no_entity_label = QtWidgets.QLabel(
            '<html><i>Please select an entity!</i></html>'
        )
        self.no_entity_label.setVisible(True)

        self.entity_browse_button = CircularButton('edit', variant='outlined')

        self.layout().addWidget(self.thumbnail_widget)
        self.layout().addWidget(self.entity_info)
        self.layout().addWidget(self.no_entity_label)
        self.layout().addWidget(QtWidgets.QLabel(), 10)
        self.layout().addWidget(self.entity_browse_button)

        # Build entity browser:

        self._entity_browser = EntityBrowser(
            self.parent(),
            self.session,
            title='CHOOSE TASK (WORKING CONTEXT)'
            if self._select_task
            else 'CHOOSE CONTEXT',
            mode=EntityBrowser.MODE_TASK
            if self._select_task
            else EntityBrowser.MODE_CONTEXT,
        )
        self.entity_browser.setMinimumWidth(600)
        if self._entity:
            self.entity_browser.entity = self._entity['parent']
        elif self._browse_context_id:
            self.entity_browser.entity_id = self._browse_context_id
        else:
            self.entity_browser.entity = None
        if self.entity_browser.entity:
            self.entity = self.entity_browser.entity

    def set_thumbnail(self, entity):
        '''Set the entity thumbnail'''
        self.thumbnail_widget.load(entity['id'])

    def post_build(self):
        self.entity_browse_button.clicked.connect(
            self._on_entity_browse_button_clicked
        )
        self.entity_found.connect(self._on_entity_found)
        self.setMaximumHeight(50)

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
            self._browsing_context = False
            return
        self.entity_found.emit(entity)

    def _on_entity_found(self, entity):
        '''Entity found callback, set entity'''
        self.entity = entity
        self._browsing_context = False

    def _on_entity_browse_button_clicked(self):
        '''Handle entity browse button clicked'''

        if self._enable_context_change:
            # Launch browser.
            if self.entity_browser.exec_():
                self.entity = self.entity_browser.entity
        else:
            # Let client decide what to do when user wants to change context
            self.change_context_clicked.emit()
