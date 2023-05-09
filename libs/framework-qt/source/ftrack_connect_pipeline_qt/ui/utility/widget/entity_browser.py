# :coding: utf-8
# :copyright: Copyright (c) 2022 ftrack
from functools import partial

import ftrack_connect_pipeline_qt.ui.utility.widget.button
from Qt import QtWidgets, QtCore, QtGui

import shiboken2

from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import Context
from ftrack_connect_pipeline_qt.ui.utility.widget.search import Search
from ftrack_connect_pipeline_qt.utils import (
    BaseThread,
    clear_layout,
    set_property,
    center_widget,
    InputEventBlockingWidget,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)
from ftrack_connect_pipeline_qt.ui.utility.widget.busy_indicator import (
    BusyIndicator,
)
from ftrack_connect_pipeline_qt.ui.utility.widget import (
    dialog,
    icon,
    scroll_area,
)


class EntityBrowser(dialog.ModalDialog):
    '''
    Dialog widget enabling entity/context browsing
    Supports to be driven from an external detached navigator browser (assembler).
    '''

    MODE_ENTITY = 1  # Pick any entity in backend (NIY)
    MODE_CONTEXT = 2  # Pick any context
    MODE_TASK = 3  # Only pick tasks

    SHOW_CHILDREN = False

    entityChanged = QtCore.Signal(
        object
    )  # External; a new context has been set
    rebuildEntityBrowser = QtCore.Signal()  # Entity browser should be rebuilt
    entitiesFetched = QtCore.Signal(
        object
    )  # The entities beneath entity has been fetched

    working = (
        False  # Flag preventing multiple user operations at the same time
    )

    @property
    def entity(self):
        '''Return the current entity'''
        return self._entity

    @entity.setter
    def entity(self, value):
        '''Set the current entity to *value*'''
        if self.working:
            return
        prev_entity = self._entity
        self._entity = value
        self.intermediate_entity = value
        if self._external_navigator is not None:
            self._external_navigator.refreshNavigator.emit()
        if (value or {}).get('id') != (prev_entity or {}).get('id'):
            if prev_entity is not None:
                self.entityChanged.emit(value)
            if self.isVisible():
                self.rebuildEntityBrowser.emit()

    @property
    def entity_id(self):
        '''Return the entity id'''
        return self._entity['id'] if self._entity else None

    @entity_id.setter
    def entity_id(self, value):
        '''Set the current entity id to *value*'''
        self.entity = self.find_context_entity(value)

    @property
    def intermediate_entity(self):
        '''Return the entity currently browsed before user has accepted (applied)'''
        return self._intermediate_entity

    @intermediate_entity.setter
    def intermediate_entity(self, value):
        '''Set the intermediate entity to value'''
        if self.working:
            return
        self._intermediate_entity = value
        self._prev_search_text = ""
        self._search.text = ""
        self._selected_entity = value
        if self.isVisible():
            # Rebuild navigator and browsing content based on current intermediate entity
            self._navigator.refreshNavigator.emit()
            self.rebuildEntityBrowser.emit()

    @property
    def mode(self):
        '''Return the entity browser mode'''
        return self._mode

    @mode.setter
    def mode(self, value):
        '''Set the entity browser mode to value'''
        if not value in [
            EntityBrowser.MODE_ENTITY,
            EntityBrowser.MODE_CONTEXT,
            EntityBrowser.MODE_TASK,
        ]:
            raise Exception("Unknown entity browser mode - !{}".format(value))
        self._mode = value

    @property
    def session(self):
        '''Return :class:`ftrack_api.session.Session`'''
        return self._session

    def __init__(self, parent, session, entity=None, mode=None, title=None):
        '''
        Initialize the entity browser

        :param parent: The parent dialog or frame
        :param session: :class:`ftrack_api.session.Session`
        :param entity: The entity to use from start
        :param mode: Set the entity browser mode
        :param title: The text to put on title bar
        '''
        self._entity = None  # The entity that has been set and applied
        self._intermediate_entity = (
            None  # The intermediate entity currently browsed
        )
        self._selected_entity = None  # The selected entity
        self._session = session
        self._external_navigator = None
        self._prev_search_text = ""
        self.working = False

        self.mode = mode or EntityBrowser.MODE_TASK

        super(EntityBrowser, self).__init__(
            parent, title=title or 'ftrack Entity Browser'
        )

        if entity:
            self.entity = entity

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)

    def pre_build(self):
        super(EntityBrowser, self).pre_build()
        # The navigator within dialog, showing intermediate entity
        self._navigator = EntityBrowserNavigator(self, is_browser=True)

    def get_content_widget(self):
        '''(Override)'''
        self._content_widget = InputEventBlockingWidget(lambda: self.working)
        self._content_widget.setLayout(QtWidgets.QVBoxLayout())
        self._content_widget.layout().setContentsMargins(1, 1, 1, 1)
        self._content_widget.layout().setSpacing(5)

        toolbar = QtWidgets.QWidget()
        toolbar.setLayout(QtWidgets.QHBoxLayout())
        toolbar.layout().setContentsMargins(0, 0, 0, 0)
        toolbar.layout().setSpacing(1)

        toolbar.layout().addWidget(self._navigator)
        toolbar.layout().addWidget(QtWidgets.QLabel(), 100)
        self._rebuild_button = CircularButton('sync')
        toolbar.layout().addWidget(self._rebuild_button)

        self._content_widget.layout().addWidget(toolbar)

        self._search = Search(collapsed=False, collapsable=False)
        self._search.inputUpdated.connect(self._on_search)
        self._content_widget.layout().addWidget(self._search)

        self._scroll = scroll_area.ScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self._content_widget.layout().addWidget(self._scroll, 100)

        return self._content_widget

    def get_approve_button(self):
        '''(Override)'''
        return (
            ftrack_connect_pipeline_qt.ui.utility.widget.button.ApproveButton(
                "APPLY CONTEXT", width=80
            )
        )

    def get_deny_button(self):
        '''(Override)'''
        return ftrack_connect_pipeline_qt.ui.utility.widget.button.DenyButton(
            "CANCEL", width=80
        )

    def post_build(self):
        super(EntityBrowser, self).post_build()

        self.rebuildEntityBrowser.connect(self.rebuild)

        self._navigator.changeEntity.connect(self._on_set_intermediate_entity)
        self._navigator.removeEntity.connect(
            self._set_parent_intermediate_entity
        )

        self._rebuild_button.clicked.connect(self.rebuild)
        self._approve_button.clicked.connect(self._on_apply)
        self._deny_button.clicked.connect(self.reject)

        self.entitiesFetched.connect(self._on_entities_fetched)

        self.resize(700, 450)

    def create_navigator(self):
        '''Create and return an external navigator widget (Assembler browser)'''
        self._external_navigator = EntityBrowserNavigator(self)
        self._external_navigator.changeEntity.connect(self._browse_parent)
        self._external_navigator.addEntity.connect(self._add_entity)
        self._external_navigator.removeEntity.connect(self._set_parent_entity)
        self._external_navigator.refreshNavigator.emit()
        return self._external_navigator

    def _browse_parent(self, entity):
        '''Browse to the parent of *entity*'''
        if self.working:
            return
        self.intermediate_entity = entity['parent'] if entity else None
        self.show()

    def _add_entity(self):
        '''Add entity were clicked in external navigator, show entity browser'''
        if self.working:
            return
        self.show()

    def _set_parent_entity(self, entity):
        '''Set the current entity to the parent of *entity*'''
        if self.working:
            return
        self.entity = entity['parent'] if entity else None

    def show(self):
        '''Show dialog, on the entity supplied'''
        self._navigator.refreshNavigator.emit()
        self.rebuildEntityBrowser.emit()
        return super(EntityBrowser, self).show()

    def exec_(self):
        '''(Override)'''
        try:
            self._navigator.refreshNavigator.emit()
            self.rebuildEntityBrowser.emit()
            return super(EntityBrowser, self).exec_()
        finally:
            # Make sure event filters are removed
            self._content_widget.stop()
            self._navigator.stop()

    def _set_parent_intermediate_entity(self, entity):
        '''Set the current intermediate entity to the parent of *entity*'''
        self.intermediate_entity = entity['parent'] if entity else None

    def find_context_entity(self, entity_id):
        '''Fetch the entity from frack based on *entity_id*'''
        context_entity = self.session.query(
            'select link, name, parent, parent.name from Context where id '
            'is "{}"'.format(entity_id)
        ).one()
        return context_entity

    def rebuild(self):
        if self.working:
            return

        self.working = True
        self.entity_widgets = []

        self._busy_indicator = BusyIndicator(False)

        self._scroll.setWidget(center_widget(self._busy_indicator, 30, 30))

        self._busy_indicator.start()

        self.update()

        # Resolve version this context is depending on in separate thread
        thread = BaseThread(
            name='fetch_entities_thread',
            target=self._fetch_entities,
            target_args=(),
        )
        thread.start()

    def _fetch_entities(self):
        '''(Run in background thread) Fetch projects/child entities'''
        signal_emitted = False
        try:
            intermediate_entity = self.intermediate_entity
            if self.intermediate_entity is None:
                # List projects
                entities = self.session.query(
                    'select id, name from Project where status=active'
                ).all()
            else:
                entities = self.session.query(
                    'select id, name{} from Context where parent.id is {}'.format(
                        ', children' if self.SHOW_CHILDREN else '',
                        intermediate_entity['id'],
                    )
                ).all()
            self.entitiesFetched.emit(entities)
            signal_emitted = True
        finally:
            if not signal_emitted:
                # Crashed, stop working to unblock
                self.working = False

    def _on_entities_fetched(self, entities):
        '''Entities has been fetch, rebuild widget'''
        try:
            entities_widget = QtWidgets.QWidget()
            entities_widget.setLayout(QtWidgets.QVBoxLayout())
            entities_widget.layout().setContentsMargins(0, 0, 0, 0)
            entities_widget.layout().setSpacing(0)

            self._busy_indicator.stop()

            self._scroll.setWidget(entities_widget)

            self.entity_widgets = []
            if (
                self.intermediate_entity is not None
                and self.intermediate_entity.get('parent') is not None
            ):
                parent_entity_widget = EntityWidget(
                    self.intermediate_entity['parent'],
                    False,
                    self,
                    is_parent=True,
                )
                parent_entity_widget.clicked.connect(
                    partial(
                        self._entity_selected,
                        self.intermediate_entity['parent'],
                    )
                )
                parent_entity_widget.doubleClicked.connect(
                    partial(
                        self._entity_selected,
                        self.intermediate_entity['parent'],
                        True,
                    )
                )
                entities_widget.layout().addWidget(parent_entity_widget)
                self.entity_widgets.append(parent_entity_widget)
            for entity in entities:
                entity_widget = EntityWidget(entity, False, self)
                entity_widget.clicked.connect(
                    partial(self._entity_selected, entity)
                )
                entity_widget.doubleClicked.connect(
                    partial(self._entity_selected, entity, True)
                )
                entities_widget.layout().addWidget(entity_widget)
                self.entity_widgets.append(entity_widget)
                if self.SHOW_CHILDREN:
                    for sub_entity in entity['children']:
                        if sub_entity.entity_type == 'Task':
                            sub_entity_widget = EntityWidget(
                                sub_entity, True, self
                            )
                            sub_entity_widget.clicked.connect(
                                partial(self._entity_selected, sub_entity)
                            )
                            entities_widget.layout().addWidget(
                                sub_entity_widget
                            )
                            self.entity_widgets.append(sub_entity_widget)

            entities_widget.layout().addWidget(QtWidgets.QLabel(), 100)

        finally:
            self.working = False

    def refresh(self):
        '''Filter visible entities on search.'''
        text = self._search.text.lower()
        for entity_widget in self.entity_widgets:
            entity_widget.setVisible(
                len(text) == 0
                or entity_widget.entity['name'].lower().find(text) > -1
            )

    def _entity_selected(self, entity, double_click=False):
        '''User has selected an entity'''
        self._selected_entity = entity
        for entity_widget in self.entity_widgets:
            set_property(
                entity_widget,
                "background",
                "selected"
                if entity_widget.entity['id'] == entity['id']
                else "",
            )
        if entity.entity_type != "Task":
            # Dive further down
            thread = BaseThread(
                name='entity_clicked_thread',
                target=self._on_set_intermediate_entity,
                target_args=[entity],
            )
            thread.start()
        else:
            self.update()
            if double_click:
                if self.mode == EntityBrowser.MODE_TASK:
                    self._on_apply()

    def _on_set_intermediate_entity(self, entity):
        '''Callback for setting the intermediate entity'''
        self.intermediate_entity = entity

    def update(self):
        '''Update entity browser'''
        # Search text changed?
        if self._search.text != self._prev_search_text:
            self.refresh()
            self._prev_search_text = self._search.text
        has_selection = False
        if self._selected_entity:
            if self.mode == EntityBrowser.MODE_CONTEXT:
                has_selection = True
            elif self.mode == EntityBrowser.MODE_TASK:
                has_selection = self._selected_entity.entity_type == 'Task'
        self._approve_button.setEnabled(has_selection)

    def _on_search(self, text):
        '''Filter list of entities - only include the ones matching text.'''
        self.update()

    def _on_apply(self):
        '''Set the immediate entity and close dialog'''
        if self.working:
            return
        self.entity = self._selected_entity
        self.done(1)


class EntityBrowserNavigator(InputEventBlockingWidget):
    '''Widget representing the path down to the current entity (intermediate if not external browser)'''

    changeEntity = QtCore.Signal(
        object
    )  # A entity navigator item has been clicked
    removeEntity = QtCore.Signal(
        object
    )  # The remove button has been clicked on an entity navigator item
    addEntity = (
        QtCore.Signal()
    )  # The plus sign button has been clicked (external navigator only)
    refreshNavigator = QtCore.Signal()  # Navigator should be refreshed
    rebuildNavigator = QtCore.Signal()  # Navigator should be rebuilt

    working = False

    @property
    def entity(self):
        '''Retreive the entity browsed in navigator'''
        return (
            self._entity_browser.intermediate_entity
            if self._is_browser
            else self._entity_browser.entity
        )

    @property
    def entity_browser(self):
        '''Return parent entity browser driving this navigator'''
        return self._entity_browser

    @property
    def session(self):
        '''Return the :class:`ftrack_api.session.Session`'''
        return self._entity_browser.session

    def __init__(
        self,
        entity_browser,
        is_browser=False,
        parent=None,
    ):
        '''
        Initialise EntityBrowser navigator widget

        :param entity_browser: :class:`~ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser.EntityBrowser` instance
        :param is_browser: If False (default), navigator is assumed to be an external navigator docked in another widget. If True, navigator resides withing the entity browser header.
        :param parent: The parent dialog or frame
        '''
        super(EntityBrowserNavigator, self).__init__(
            lambda: self.working or self._entity_browser.working, parent=parent
        )
        self._entity_browser = entity_browser
        self._is_browser = is_browser

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(self.create_layout())

    def create_layout(self):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        return layout

    def build(self):
        pass

    def post_build(self):
        self.setMinimumHeight(36)
        self.setMaximumHeight(36)
        self.refreshNavigator.connect(self.refresh)
        self.rebuildNavigator.connect(self.rebuild)

    def refresh(self):
        '''Rebuild the navigator'''

        self.working = True

        # self.setLayout(self.create_layout())
        clear_layout(self.layout())

        thread = BaseThread(
            name='fetch_entities_thread',
            target=self._on_entities_fetched,
            target_args=(),
        )
        thread.start()

    def _on_entities_fetched(self):
        self.rebuildNavigator.emit()

    def rebuild(self):
        '''Rebuild the navigator'''
        try:
            # Rebuild widget

            if self._is_browser:
                home_button = HomeContextButton()
                home_button.clicked.connect(self._on_go_home)
                self.layout().addWidget(home_button)

                l_arrow = QtWidgets.QLabel()
                l_arrow.setPixmap(
                    icon.MaterialIcon('chevron-right', color='#676B70').pixmap(
                        QtCore.QSize(16, 16)
                    )
                )
                l_arrow.setMinimumSize(QtCore.QSize(16, 16))
                self.layout().addWidget(l_arrow)

            add_enabled = not self._is_browser

            if self.entity:
                for index, link in enumerate(self.entity['link']):
                    button = NavigationEntityButton(link)
                    button.clicked.connect(
                        partial(self._on_entity_changed, button.link_entity)
                    )
                    set_property(
                        button, 'first', 'true' if index == 0 else 'false'
                    )
                    if link['type'] != 'Project':
                        button.remove_button.released.connect(
                            partial(self._on_remove_entity, link)
                        )
                    self.layout().addWidget(button)

                    if index < len(self.entity['link']) - 1:
                        l_arrow = QtWidgets.QLabel()
                        l_arrow.setPixmap(
                            icon.MaterialIcon(
                                'chevron-right', color='#676B70'
                            ).pixmap(QtCore.QSize(16, 16))
                        )
                        l_arrow.setMinimumSize(QtCore.QSize(16, 16))
                        self.layout().addWidget(l_arrow)

            if add_enabled:
                if self.entity:
                    l_arrow = QtWidgets.QLabel()
                    l_arrow.setPixmap(
                        icon.MaterialIcon(
                            'chevron-right', color='#676B70'
                        ).pixmap(QtCore.QSize(16, 16))
                    )
                    l_arrow.setMinimumSize(QtCore.QSize(16, 16))
                    self.layout().addWidget(l_arrow)

                add_button = AddContextButton()
                add_button.clicked.connect(self._on_add_entity)
                self.layout().addWidget(add_button)

            self.layout().addWidget(QtWidgets.QLabel(), 100)
        finally:
            self.working = False

    def _on_go_home(self):
        if self.working or self._entity_browser.working:
            return
        self.changeEntity.emit(None)

    def _on_add_entity(self, **kwargs):
        '''The add entity button were clicked in navigator'''
        if self.working or self._entity_browser.working:
            return
        self.addEntity.emit()

    def _on_entity_changed(self, link_entity):
        '''A navigator item has been clicked.'''
        if self.working or self._entity_browser.working:
            return
        self.changeEntity.emit(
            self._entity_browser.find_context_entity(link_entity['id'])
        )

    def _on_remove_entity(self, link_entity):
        if self.working or self._entity_browser.working:
            return
        self.removeEntity.emit(
            self._entity_browser.find_context_entity(link_entity['id'])
        )


class NavigationEntityButton(QtWidgets.QFrame):
    '''A button representing a context within the navigator.'''

    clicked = QtCore.Signal()

    def __init__(self, link_entity, parent=None):
        super(NavigationEntityButton, self).__init__(parent=parent)
        self.link_entity = link_entity
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(3, 0, 3, 0)
        self.layout().setSpacing(4)

    def build(self):
        label = QtWidgets.QLabel(self.link_entity['name'])
        self.layout().addWidget(label)
        if self.link_entity['type'] != 'Project':
            self.layout().addStretch()
            self.remove_button = QtWidgets.QPushButton(
                icon.MaterialIcon('close', color='#94979a'), ""
            )
            self.remove_button.setFixedSize(8, 8)
            self.remove_button.setStyleSheet(
                '''
            QPushButton {
                border: none; background: transparent;
            }
            QPushButton:hover {
                background: gray;
            }
'''
            )
            self.layout().addWidget(self.remove_button)

    def post_build(self):
        fm = QtGui.QFontMetrics(self.font())
        self.setMinimumWidth(
            fm.horizontalAdvance(self.link_entity['name'])
            + (4 if self.link_entity['type'] != 'Project' else 0)
        )
        self.setMinimumHeight(25)
        self.setMaximumHeight(25)

    def mousePressEvent(self, event):
        self.clicked.emit()
        return super(NavigationEntityButton, self).mousePressEvent(event)


class EntityWidget(QtWidgets.QFrame):
    '''A button representing a context within the navigator.'''

    clicked = QtCore.Signal()
    doubleClicked = QtCore.Signal()

    def __init__(
        self, entity, is_sub_task, entity_browser, parent=None, is_parent=False
    ):
        super(EntityWidget, self).__init__(parent=parent)
        self.entity = entity
        self.is_parent = is_parent
        self.is_sub_task = is_sub_task
        self._entity_browser = entity_browser
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(3, 1, 1, 1)
        self.layout().setSpacing(2)

    def build(self):
        self.thumbnail_widget = Context(self.entity.session)
        self.thumbnail_widget.setMinimumWidth(71)
        self.thumbnail_widget.setMinimumHeight(40)
        self.thumbnail_widget.setMaximumWidth(71)
        self.thumbnail_widget.setMaximumHeight(40)
        if not self.is_parent:
            self.thumbnail_widget.load(self.entity['id'])
        self.layout().addWidget(self.thumbnail_widget)

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(QtWidgets.QVBoxLayout())
        central_widget.layout().setContentsMargins(3, 0, 0, 0)
        central_widget.layout().setSpacing(0)

        # Context name
        label = QtWidgets.QLabel(
            self.entity['name'] if not self.is_parent else '..'
        )
        label.setObjectName('h3' if not self.is_parent else 'h2')
        central_widget.layout().addWidget(label)

        lower_widget = QtWidgets.QWidget()
        lower_widget.setLayout(QtWidgets.QHBoxLayout())
        lower_widget.layout().setContentsMargins(3, 0, 0, 0)
        lower_widget.layout().setSpacing(0)

        if self.is_sub_task and not self.is_parent:
            # Sub path
            sub_path = QtWidgets.QLabel(
                '.. / {}'.format(self.entity['parent']['name'])
            )
            sub_path.setObjectName('gray')
            lower_widget.layout().addWidget(sub_path)

        if not self.is_parent:
            type_widget = TypeWidget(self.entity)
            lower_widget.layout().addWidget(type_widget)

        lower_widget.layout().addWidget(QtWidgets.QLabel(), 100)

        central_widget.layout().addWidget(lower_widget)

        self.layout().addWidget(central_widget, 100)

        if self.entity.entity_type != 'Task' and not self.is_parent:
            l_arrow = QtWidgets.QLabel()
            l_arrow.setPixmap(
                icon.MaterialIcon('chevron-right', color='#676B70').pixmap(
                    QtCore.QSize(16, 16)
                )
            )
            l_arrow.setMinimumSize(QtCore.QSize(16, 16))
            self.layout().addWidget(l_arrow)

    def post_build(self):
        if self.entity.entity_type == "Task":
            # Show task status
            self.setStyleSheet(
                '''
                EntityWidget {
                    border-right: 3px solid %s;
                }'''
                % (self.entity['status']['color'])
            )
        self.setMinimumHeight(45 if not self.is_parent else 20)
        self.setMaximumHeight(45 if not self.is_parent else 20)

    def mousePressEvent(self, event):
        if not shiboken2.isValid(self) or not shiboken2.isValid(
            super(EntityWidget, self)
        ):
            # Widget has been destroyed
            return
        retval = super(EntityWidget, self).mousePressEvent(event)
        if (
            self._entity_browser is None
            or self._entity_browser.working is False
        ):
            self.clicked.emit()
        return retval

    def mouseDoubleClickEvent(self, event):
        if not shiboken2.isValid(self) or not shiboken2.isValid(
            super(EntityWidget, self)
        ):
            # Widget has been destroyed
            return
        return super(EntityWidget, self).mouseDoubleClickEvent(event)
        self.doubleClicked.emit()


class AddContextButton(CircularButton):
    def __init__(self, parent=None):
        super(AddContextButton, self).__init__('add', '#eee', parent=parent)

    def get_border_style(self, color):
        return '''            
            border: 1 dashed #2b3036;
            border-radius: 16px;
        '''


class HomeContextButton(CircularButton):
    def __init__(self, parent=None):
        super(HomeContextButton, self).__init__('home', '#eee', parent=parent)

    def get_border_style(self, color):
        return '''            
            border: 1 dashed #2b3036;
            border-radius: 16px;
        '''


class TypeWidget(QtWidgets.QFrame):
    '''Widget representing the entity type with text and icon'''

    def __init__(self, entity, parent=None):
        super(TypeWidget, self).__init__(parent=parent)
        self._entity = entity
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(3, 0, 7, 0)
        self.layout().setSpacing(2)

    def build(self):
        l_icon = QtWidgets.QLabel()

        if self._entity.entity_type != 'Task':
            icon_name = "help_outline"
            if self._entity.entity_type == 'Project':
                icon_name = "home"
            elif self._entity.entity_type == 'Folder':
                icon_name = "folder"
            elif self._entity.entity_type == 'Episode':
                icon_name = "smart_display"
            elif self._entity.entity_type == 'Sequence':
                icon_name = "movie"
            elif self._entity.entity_type == 'Shot':
                icon_name = "movie"
            elif self._entity.entity_type == "AssetBuild":
                icon_name = "table_chart"
            l_icon.setPixmap(
                icon.MaterialIcon(icon_name, color='#FFDD86').pixmap(
                    QtCore.QSize(16, 16)
                )
            )
        else:
            l_icon.setPixmap(
                icon.MaterialIcon(
                    'assignment_turned_in',
                    variant='outlined',
                    color=self._entity['type']['color'],
                ).pixmap(QtCore.QSize(14, 14))
            )
        self.layout().addWidget(l_icon)
        l_name = QtWidgets.QLabel(
            self._entity.entity_type
            if self._entity.entity_type != 'Task'
            else self._entity['type']['name']
        )
        self.layout().addWidget(l_name)

    def post_build(self):
        self.setMinimumHeight(25)
        self.setMaximumHeight(25)
