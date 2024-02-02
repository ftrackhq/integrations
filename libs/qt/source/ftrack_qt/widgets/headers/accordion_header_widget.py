# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.icons import (
    ArrowMaterialIconWidget,
    MaterialIcon,
    StatusMaterialIconWidget,
)
from ftrack_qt.widgets.lines import LineWidget
from ftrack_qt.widgets.buttons import OptionsButton


class AccordionHeaderWidget(QtWidgets.QFrame):
    '''Container for accordion header - holding checkbox, title, user content
    and expander button.'''

    clicked = QtCore.Signal(object)  # User header click
    arrow_clicked = QtCore.Signal(object)  # User header click
    checkbox_status_changed = QtCore.Signal(object)

    @property
    def title(self):
        return self._title

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

    def __init__(
        self,
        title=None,
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
        self._title_label = QtWidgets.QLabel(self.title or '')
        self._title_label.setObjectName('borderless')
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
        self._status_label.setObjectName('color-primary')
        content_layout.addWidget(self._status_label)
        content_layout.addStretch()
        content_layout.addWidget(LineWidget(horizontal=True))
        # add options widget
        self._options_button = OptionsButton(
            self.title, MaterialIcon('settings', color='gray')
        )
        self._options_button.setObjectName('borderless')
        content_layout.addWidget(LineWidget(horizontal=True))
        # add status icon
        self._status_icon = StatusMaterialIconWidget('check')
        self._status_icon.setObjectName('borderless')

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
