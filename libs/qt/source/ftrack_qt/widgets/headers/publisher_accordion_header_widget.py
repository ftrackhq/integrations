# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.headers import (
    AccordionHeaderWidget,
)
from ftrack_qt.widgets.icons import (
    MaterialIcon,
    StatusMaterialIconWidget,
)


class PublisherAccordionHeaderWidget(AccordionHeaderWidget):
    '''Extended header with options and status icon, for publisher accordion'''

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
        self._status = None
        self._options_button = None
        self._status_icon = None
        super(PublisherAccordionHeaderWidget, self).__init__(
            title=title,
            checkable=checkable,
            checked=checked,
            show_checkbox=show_checkbox,
            collapsable=collapsable,
            collapsed=collapsed,
            parent=parent,
        )

    def build_content(self):
        result = QtWidgets.QWidget()
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        result.setLayout(content_layout)

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
        content_layout.addWidget(self._options_button)
        content_layout.addWidget(LineWidget(horizontal=True))
        # add status icon
        self._status_icon = StatusMaterialIconWidget('check')
        self._status_icon.setObjectName('borderless')
        content_layout.addWidget(self._status_icon)
        return result

    def post_build(self):
        super(PublisherAccordionHeaderWidget, self).post_build()
        self._checkbox.stateChanged.connect(self._on_checkbox_status_changed)

    def _on_checkbox_status_changed(self):
        self._checked = self._checkbox.isChecked()
        self._title_label.setEnabled(self._checked)
        self._header_content_widget.setEnabled(self._checked)
        self.checkbox_status_changed.emit(self._checked)

    def add_option_widget(self, widget, section_name):
        self._options_button.add_widget(widget, section_name)
