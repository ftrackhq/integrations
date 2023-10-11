# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_framework_widget.widget import FrameworkWidget

from ftrack_qt.widgets.selectors import AssetSelector
from ftrack_qt.widgets.selectors import StatusSelector
from ftrack_qt.widgets.lines import LineWidget


class PhotoshopPublishContextWidget(FrameworkWidget, QtWidgets.QWidget):
    '''Main class to represent a context widget on a photoshop publisher'''

    name = 'photoshop_publisher_context_selector'
    ui_type = 'qt'

    def __init__(
        self,
        event_manager,
        client_id,
        context_id,
        plugin_config,
        dialog_connect_methods_callback,
        dialog_property_getter_connection_callback,
        parent=None,
    ):
        '''initialise PhotoshopPublishContextWidget'''
        self._description_input = None
        self._note_input = None

        QtWidgets.QWidget.__init__(self, parent=parent)
        FrameworkWidget.__init__(
            self,
            event_manager,
            client_id,
            context_id,
            plugin_config,
            dialog_connect_methods_callback,
            dialog_property_getter_connection_callback,
            parent=parent,
        )

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        self.setLayout(layout)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )

    def build(self):
        '''build function widgets.'''

        # Build description widget
        description_layout = QtWidgets.QHBoxLayout()
        description_layout.setContentsMargins(0, 0, 0, 0)

        # Provide context id
        self.set_plugin_option('context_id', self.context_id)

        # Build description label
        description_label = QtWidgets.QLabel('Description')
        description_label.setObjectName('gray')
        description_label.setAlignment(QtCore.Qt.AlignTop)
        self._description_input = QtWidgets.QLineEdit()
        self._description_input.setMaximumHeight(40)
        self._description_input.setPlaceholderText("Type a description...")

        description_layout.addWidget(description_label)
        description_layout.addWidget(self._description_input)

        # Build notes widget
        notes_layout = QtWidgets.QHBoxLayout()
        notes_layout.setContentsMargins(0, 0, 0, 0)

        notes_label = QtWidgets.QLabel('Note')
        notes_label.setObjectName('gray')
        notes_label.setAlignment(QtCore.Qt.AlignTop)
        self._note_input = QtWidgets.QTextEdit()
        self._note_input.setMaximumHeight(40)
        self._note_input.setPlaceholderText("Type a Note...")

        notes_layout.addWidget(notes_label)
        notes_layout.addWidget(self._note_input)

        # Add the widgets to the layout
        self.layout().addLayout(description_layout)
        self.layout().addLayout(notes_layout)

    def post_build(self):
        '''hook events'''
        self._description_input.textChanged.connect(
            self._on_description_updated
        )
        self._note_input.textChanged.connect(self._on_note_updated)

    def _on_description_updated(self):
        '''Updates the option dictionary with current text when
        textChanged of comments_input event is triggered'''
        current_text = self._description_input.text()
        self.set_plugin_option('comment', current_text)

    def _on_note_updated(self):
        '''Updates the option dictionary with current text when
        textChanged of comments_input event is triggered'''
        current_text = self._note_input.toPlainText()
        self.set_plugin_option('note', current_text)
