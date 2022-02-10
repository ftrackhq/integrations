# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
from functools import partial

import qtawesome as qta

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline.utils import get_current_context_id
from ftrack_connect_pipeline_qt.ui.utility.widget.entity_info import EntityInfo
import ftrack_connect_pipeline_qt.ui.utility.widget.entity_browser as entityBrowser
from ftrack_connect_pipeline_qt.ui.utility.widget.thumbnail import Context
from ftrack_connect_pipeline_qt.utils import clear_layout
from ftrack_connect_pipeline_qt.ui.utility.widget.circular_button import (
    CircularButton,
)


class ContextBrowser(QtWidgets.QWidget):
    entityChanged = QtCore.Signal(
        object
    )  # External; a new context has been set

    clickedEntity = QtCore.Signal(
        object
    )  # Internal; A entity chip has been clicked
    addEntity = (
        QtCore.Signal()
    )  # Internal; The plus sign button has been clicked

    @property
    def entity(self):
        return self._entity

    def __init__(
        self,
        entity,
        session,
        parent=None,
    ):
        '''Initialise ContextSelector widget with the *current_entity* and
        *parent* widget.
        '''
        super(ContextBrowser, self).__init__(parent=parent)
        self._entity = entity
        self.session = session

        self.pre_build()
        self.build()
        self.post_build()

        self.set_entity(self._entity)

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        pass

    def set_thumbnail(self, entity):
        self.thumbnail_widget.load(entity['id'])

    def post_build(self):
        self.clickedEntity.connect(self._show_entity_picker)
        self.addEntity.connect(partial(self._show_entity_picker, None))
        self.setMaximumHeight(36)

    def set_entity(self, entity):
        '''Set the *entity* for the view.'''
        clear_layout(self.layout())
        if not entity:
            # Need one entity, choose first active project
            entity = self.session.query(
                'select link, name, parent, parent.name from Project where status is active'
            ).first()
            if entity is None:
                # Any project
                entity = self.session.query(
                    'select link, name from Project'
                ).first()
                if entity is None:
                    self.layout().addWidget(
                        'No entity given, and no project found!'
                    )
                    raise Exception('No entity given, and no project found!')
        self._entity = entity
        # Rebuild widget
        for index, link in enumerate(self._entity['link']):
            button = ContextButton(link)
            button.clicked.connect(
                partial(self._on_entity_changed, button.link_entity)
            )
            if link['type'] != 'Project':
                button.remove_button.clicked.connect(
                    partial(self._on_remove_entity, link)
                )
            self.layout().addWidget(button)
            l_arrow = QtWidgets.QLabel()
            l_arrow.setPixmap(
                qta.icon('mdi6.chevron-right', color='#676B70').pixmap(
                    QtCore.QSize(16, 16)
                )
            )
            self.layout().addWidget(l_arrow)

        add_button = AddContextButton()
        add_button.clicked.connect(self._on_add_entity)
        self.layout().addWidget(add_button)

        self.entityChanged.emit(entity)
        self.layout().addWidget(QtWidgets.QLabel(), 1000)

    def _on_entity_changed(self, link_entity):
        self.clickedEntity.emit(self.find_context_entity(link_entity['id']))

    def _on_add_entity(self, unused_linked_entity):
        self.addEntity.emit()

    def _on_remove_entity(self, link_entity):
        print('@@@ _on_remove_entity({})'.format(link_entity))

    def find_context_entity(self, context_id):
        context_entity = self.session.query(
            'select link, name , parent, parent.name from Context where id '
            'is "{}"'.format(context_id)
        ).one()
        return context_entity

    def _show_entity_picker(self, clicked_entity):
        print('@@@ _show_entity_picker({})'.format(clicked_entity))


class ContextButton(QtWidgets.QFrame):
    clicked = QtCore.Signal()

    def __init__(self, link_entity, parent=None):
        super(ContextButton, self).__init__(parent=parent)
        self.link_entity = link_entity
        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(3, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        label = QtWidgets.QLabel(self.link_entity['name'])
        self.layout().addWidget(label)
        if self.link_entity['type'] != 'Project':
            self.layout().addStretch()
            self.remove_button = QtWidgets.QPushButton(
                qta.icon('mdi6.close', color='#94979a', size=8), ""
            )
            self.remove_button.setStyleSheet(
                'border: none; background: transparent;'
            )
            self.layout().addWidget(self.remove_button)

    def post_build(self):
        fm = QtGui.QFontMetrics(self.font())
        self.setMinimumWidth(
            fm.horizontalAdvance(self.link_entity['name'])
            + (4 if self.link_entity['type'] != 'Project' else 0)
        )
        self.setMinimumHeight(32)

    def mousePressEvent(self, event):
        self.clicked.emit()
        return super(ContextButton, self).mousePressEvent(event)


class AddContextButton(CircularButton):
    def __init__(self, parent=None):
        super(AddContextButton, self).__init__('plus', '#eee', parent=parent)

    def get_border_style(self, color):
        return '''            
            border: 1 dashed #2b3036;
            border-radius: 16px;
        '''.format()
