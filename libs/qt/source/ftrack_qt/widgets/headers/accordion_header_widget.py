# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from ftrack_qt.widgets.icons import (
    ArrowMaterialIconWidget,
    MaterialIcon,
    StatusMaterialIconWidget,
)
from ftrack_qt.widgets.lines import LineWidget
from ftrack_qt.widgets.buttons import OptionsButton
from ftrack_qt.widgets.labels import EditableLabel


class AccordionHeaderWidget(QtWidgets.QFrame):
    '''Container for accordion header - holding checkbox, title, user content
    and expander button.'''

    clicked = QtCore.Signal(object)  # User header click
    arrow_clicked = QtCore.Signal(object)  # User header click
    checkbox_status_changed = QtCore.Signal(object)
    show_options_overlay = QtCore.Signal(object)
    hide_options_overlay = QtCore.Signal()
    title_changed = QtCore.Signal(object)
    title_edited = QtCore.Signal(object)

    @property
    def title(self):
        if self._title_label:
            return self._title_label.text()
        return self._title

    @property
    def editable_title(self):
        return self._editable_title

    @property
    def checkable(self):
        return self._checkable

    @property
    def checked(self):
        return self._checked

    @property
    def show_checkbox(self):
        return self._show_checkbox

    @property
    def collapsable(self):
        return self._collapsable

    @property
    def collapsed(self):
        return self._collapsed

    @property
    def options_button(self):
        return self._options_button

    def __init__(
        self,
        title=None,
        editable_title=False,
        checkable=False,
        checked=True,
        show_checkbox=False,
        collapsable=True,
        collapsed=True,
        parent=None,
    ):
        '''
        Initialize header widget

        :param title: The default title to give header
        :param parent: The parent dialog or frame
        '''
        super(AccordionHeaderWidget, self).__init__(parent=parent)

        self._title = title
        self._editable_title = editable_title
        self._checkable = checkable
        self._checked = checked
        self._show_checkbox = show_checkbox
        self._collapsable = collapsable
        self._collapsed = collapsed

        self._checkbox = None
        self._title_label = None
        self._header_content_widget = None
        self._arrow = None
        self._status = None
        self._options_button = None
        self._status_icon = None

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setMinimumHeight(24)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(2, 0, 5, 0)
        self.layout().setSpacing(10)

    def build(self):
        # Create checkbox
        self._checkbox = QtWidgets.QCheckBox()
        self._checkbox.setEnabled(self.checkable)
        self._checkbox.setChecked(self.checked)
        self._checkbox.setVisible(self.show_checkbox)

        # Create title
        # TODO: we should be able to double click in order to edit the label in
        #  case the editable is true. (So it will look better)
        self._title_label = EditableLabel(
            text=self.title, editable=self.editable_title
        )
        if not self.title:
            self._title_label.hide()

        # Create Content
        self._header_content_widget = QtWidgets.QWidget()
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self._header_content_widget.setLayout(content_layout)

        # Add Status label widget in context Widget
        self._status_label = QtWidgets.QLabel()
        content_layout.addWidget(self._status_label)
        content_layout.addStretch()
        content_layout.addWidget(LineWidget(horizontal=True))
        # add options widget
        self._options_button = OptionsButton(
            self.title, MaterialIcon('settings', color='gray')
        )
        self._options_button.setProperty('borderless', True)
        content_layout.addWidget(LineWidget(horizontal=True))
        # add status icon
        self._status_icon = StatusMaterialIconWidget('check')

        # Create Arrow
        self._arrow = ArrowMaterialIconWidget(None)
        self.update_arrow_icon(self.collapsed)
        self._arrow.setVisible(self.collapsable)

        self.layout().addWidget(self._checkbox)
        self.layout().addWidget(self._title_label)
        self.layout().addWidget(self._header_content_widget, 10)
        self.layout().addWidget(self._options_button)
        self.layout().addWidget(self._status_icon)
        self.layout().addWidget(self._arrow)

    def post_build(self):
        self._checkbox.stateChanged.connect(self._on_checkbox_status_changed)
        self._arrow.clicked.connect(self._on_arrow_clicked)
        self._options_button.show_overlay_signal.connect(
            self.on_show_options_callback
        )
        self._options_button.hide_overlay_signal.connect(
            self.on_hide_options_callback
        )
        self._title_label.editingFinished.connect(self._on_title_edited)

    def on_show_options_callback(self, widget):
        self.show_options_overlay.emit(widget)

    def on_hide_options_callback(self):
        self.hide_options_overlay.emit()

    def add_option_widget(self, widget, section_name):
        self._options_button.add_widget(widget, section_name)

    def _on_checkbox_status_changed(self):
        self._checked = self._checkbox.isChecked()
        self._title_label.setEnabled(self._checked)
        self._header_content_widget.setEnabled(self._checked)
        self.checkbox_status_changed.emit(self._checked)

    def _on_arrow_clicked(self, event):
        self.arrow_clicked.emit(event)

    def update_arrow_icon(self, collapsed):
        '''Update the arrow icon based on collapse state'''
        if collapsed:
            icon_name = 'keyboard_arrow_down'
        else:
            icon_name = 'keyboard_arrow_up'
        self._arrow.set_icon(name=icon_name)
        self._collapsed = collapsed

    def mousePressEvent(self, event):
        '''(Override)'''
        self.clicked.emit(event)
        return super(AccordionHeaderWidget, self).mousePressEvent(event)

    def set_status(self, status, message):
        '''Set status message within header, to be implemented by child'''
        pass

    def _on_title_changed(self):
        '''
        Emit signal when title is changed
        '''
        self.title_changed.emit(self._title_label.text())

    def _on_title_edited(self):
        '''
        Emit signal when title is changed
        '''
        self.title_edited.emit(self._title_label.text())

    def set_title(self, new_title):
        '''
        Set the title of the header to *new_title*
        '''
        self._title_label.setText(new_title)
        self._on_title_changed()

    def teardown(self):
        '''Teardown the options button - properly cleanup the options overlay'''
        self._options_button.teardown()
        self._options_button.deleteLater()
