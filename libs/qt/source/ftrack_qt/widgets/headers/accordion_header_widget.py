# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_qt.widgets.icons import (
    ArrowMaterialIconWidget,
)


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

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setMinimumHeight(24)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(2, 0, 5, 0)
        self.layout().setSpacing(10)

    def build_content(self):
        '''Additional header custom content, to be implemented by subclass'''
        result = QtWidgets.QWidget()
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        result.setLayout(content_layout)

        return result

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
        self._header_content_widget = self.build_content()

        # Create Arrow
        self._arrow = ArrowMaterialIconWidget(None)
        self.update_arrow_icon(self.collapsed)
        self._arrow.setVisible(self.collapsable)

        self.layout().addWidget(self._checkbox)
        self.layout().addWidget(self._title_label)
        self.layout().addWidget(self._header_content_widget, 10)
        self.layout().addWidget(self._arrow)

    def post_build(self):
        self._arrow.clicked.connect(self._on_arrow_clicked)

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
