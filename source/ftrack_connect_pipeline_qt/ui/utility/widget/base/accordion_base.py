# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline import constants as pipeline_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.icon import (
    MaterialIconWidget,
)
from ftrack_connect_pipeline_qt.utils import set_property


class AccordionBaseWidget(QtWidgets.QFrame):
    '''A utility accordion widget providing a header which can be expanded to show content'''

    clicked = QtCore.Signal(object)  # Emitted when accordion is clicked
    doubleClicked = QtCore.Signal(
        object
    )  # Emitted when accordion is double clicked
    checkedStateChanged = QtCore.Signal(
        object
    )  # Emitted when checked state changed

    SELECT_MODE_NONE = -1  # Not selectable
    SELECT_MODE_LIST = 0  # Only list selection mode

    CHECK_MODE_NONE = -1  # Not checkable and not showing checkbox
    CHECK_MODE_CHECKBOX = 0  # Checkable and visible
    CHECK_MODE_CHECKBOX_DISABLED = 1  # Visible but not checkable

    def on_collapse(self, collapsed):
        '''(Optional) To be overridden by child'''
        pass

    def init_header_content(self, header_widget, collapsed):
        '''To be overridden by child'''
        header_layout = QtWidgets.QHBoxLayout()
        header_widget.setLayout(header_layout)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        header_layout.addStretch()

    def init_content(self, content_layout):
        '''(Optional) To be overridden by child'''
        pass

    @property
    def title(self):
        '''Return the title text shown in header by default'''
        return self._title

    @property
    def select_mode(self):
        '''Return the current selection mode'''
        return self._select_mode

    @property
    def check_mode(self):
        '''Return the current check (box) mode'''
        return self._check_mode

    @property
    def checkable(self):
        '''Return True if accordion is checkable with a checkbox'''
        return self._check_mode == self.CHECK_MODE_CHECKBOX

    @checkable.setter
    def checkable(self, value):
        '''Set the checkable property'''
        self._check_mode = (
            self.CHECK_MODE_CHECKBOX
            if value
            else self.CHECK_MODE_CHECKBOX_DISABLED
        )
        if self.header and self.header.checkbox:
            self.header.checkbox.setEnabled(
                self._check_mode == self.CHECK_MODE_CHECKBOX
            )

    @property
    def collapsed(self):
        '''Return True if accordion is collapsed - content hidden (default)'''
        return self._collapsed

    @property
    def collapsable(self):
        '''Return True if accordion is collapsable - content can be hidden (default)'''
        return self._collapsable

    @property
    def selected(self):
        '''Return True if accordion is selected'''
        return self._selected

    @selected.setter
    def selected(self, value):
        '''Set accordion selected property'''
        self._selected = value

    @property
    def checked(self):
        '''(Checkable) Return True if checked'''
        return self._checked

    @checked.setter
    def checked(self, value):
        '''Set the checked property'''
        if self.isEnabled():
            prev_checked = self._checked
            self._checked = value
            if self.header:
                if self.check_mode == self.CHECK_MODE_CHECKBOX:
                    self.header.checkbox.setChecked(value)
                self.header.title_label.setEnabled(self._checked)
            self.enable_content()
            if self._checked != prev_checked:
                self.checkedStateChanged.emit(self)

    @property
    def header(self):
        '''Return header widget'''
        return self._header

    @property
    def content(self):
        '''Return content widget'''
        return self._content

    @property
    def event_manager(self):
        '''Return the event manager'''
        return self._event_manager

    @property
    def session(self):
        '''Return the session from event manager'''
        return self._event_manager.session

    def __init__(
        self,
        select_mode,
        check_mode,
        event_manager=None,
        title=None,
        selected=False,
        checked=True,
        collapsable=True,
        collapsed=True,
        docked=False,
        parent=None,
    ):
        '''
        Initialize base accordion widget

        :param select_mode: Mode telling if accordion should be selectable or not
        :param check_mode: Mode telling if accordion should be checkale or not
        :param event_manager: :class:`~ftrack_connect_pipeline.event.EventManager` instance
        :param title: The default title text to show in accordion header
        :param selected: Flag telling if accordion should be initially selected or not
        :param checked: Flag telling if accordion should be initially checked or not
        :param collapsable: Flag telling if accordion is collapsable or not
        :param collapsed: Flag telling if accordion should be initially collapsed or not
        :param docked: Flag telling if accordion is docked in DCC or within an ftrack dialog - drives the style
        :param parent:  the parent dialog or frame
        '''
        super(AccordionBaseWidget, self).__init__(parent=parent)

        self._select_mode = select_mode
        self._check_mode = check_mode

        self._event_manager = event_manager
        self._reference_widget = None
        self._header = None
        self._content = None
        self._title = title
        self._widgets = {}
        self._inner_widget_status = {}
        self._selected = selected
        self._checked = checked
        self._collapsed = collapsed
        self._checked = checked
        self._collapsable = collapsable
        self._docked = docked

        self.pre_build()
        self.build()
        self.post_build()

    def set_status(self, status, message):
        self._header.set_status(status, message)

    def pre_build(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

    def build(self):
        self._indicator_widget = QtWidgets.QFrame()
        self._indicator_widget.setMaximumWidth(4)
        self._indicator_widget.setMinimumWidth(4)
        self._indicator_widget.setVisible(False)

        self.layout().addWidget(self._indicator_widget)

        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(QtWidgets.QVBoxLayout())
        main_widget.layout().setAlignment(QtCore.Qt.AlignTop)
        main_widget.layout().setContentsMargins(0, 0, 0, 0)
        main_widget.layout().setSpacing(1)

        main_widget.layout().addWidget(self.init_header(self._title))

        self._init_content()
        main_widget.layout().addWidget(self._content)

        self.layout().addWidget(main_widget)

    def post_build(self):
        if self.check_mode != self.CHECK_MODE_NONE:
            self.header.checkbox.stateChanged.connect(
                self._on_header_checkbox_checked
            )
        self.header.clicked.connect(self._on_header_clicked)
        self.header.arrow.clicked.connect(self._on_header_arrow_clicked)
        self._content.setVisible(not self._collapsed)
        if self.check_mode != self.CHECK_MODE_NONE:
            self.enable_content()

    def init_header(self, title):
        '''Initialize the header widget'''
        self._header = AccordionHeaderWidget(self, title=title)
        return self._header

    def _init_content(self):
        '''Initialize the content'''
        self._content = QtWidgets.QFrame()
        self.content.setLayout(QtWidgets.QVBoxLayout())

        self.content.layout().setContentsMargins(2, 2, 2, 2)
        self.content.layout().setSpacing(0)

        self.init_content(self.content.layout())

        return self._content

    def add_widget(self, widget):
        '''Add widget to content'''
        self._content.layout().addWidget(widget)

    def count_widgets(self):
        '''Return the number of widgets within the content'''
        return self._content.layout().count()

    def get_widget_at(self, index):
        '''Return the content widget at *index*'''
        return self._content.layout().itemAt(index).widget()

    def set_selected(self, selected):
        '''Set selected property to *selected*, returns True is selection changed'''
        retval = False
        if self.isEnabled():
            if self._selected != selected:
                retval = True
            self._selected = selected
            self.update_accordion()
        return retval

    def enable_content(self):
        '''Enable content widget depending on if accordion is checked or not'''
        if self._content:
            self._content.setEnabled(self.checked)

    def paint_title(self, color):
        '''Put a foreground *color* on header title label'''
        self._header._title_label.setStyleSheet("color: {}".format(color))

    def set_indicator_color(self, color):
        '''Set the left indicator visibility depending on *color*'''
        set_property(
            self._indicator_widget,
            'indicator',
            color or 'green',
        )
        if not self._indicator_widget.isVisible():
            self._indicator_widget.setVisible(True)

    def _on_header_checkbox_checked(self):
        '''Callback on enable checkbox user interaction'''
        self.checked = self.header.checkbox.isChecked()

    def _on_header_clicked(self, event):
        '''Callback on header user click'''
        if self._select_mode == self.SELECT_MODE_NONE:
            if event.button() != QtCore.Qt.RightButton:
                self.toggle_collapsed()

    def _on_header_arrow_clicked(self, event):
        '''Callback on header arrow user click'''
        if self._select_mode == self.SELECT_MODE_LIST:
            # This is the way to collapse
            self.toggle_collapsed()

    def toggle_collapsed(self):
        '''Toggle the accordion collapsed state'''
        self._collapsed = not self._collapsed
        self.header.update_arrow_icon(int(self.collapsed))
        self.on_collapse(self.collapsed)
        self._content.setVisible(not self._collapsed)

    def mousePressEvent(self, event):
        '''(Override)'''
        self.clicked.emit(event)
        self.on_click(event)
        return super(AccordionBaseWidget, self).mousePressEvent(event)

    def on_click(self, event):
        '''Callback on accordion user click, to be overridden by child'''
        pass

    def mouseDoubleClickEvent(self, event):
        '''(Override)'''
        self.doubleClicked.emit(event)
        self.on_double_click(event)
        return super(AccordionBaseWidget, self).mouseDoubleClickEvent(event)

    def on_double_click(self, event):
        '''Callback on accordion user double click, to be overridden by child'''
        self.toggle_collapsed()

    def update_accordion(self):
        '''Update accordion background depending on selection state'''
        if self._select_mode == self.SELECT_MODE_LIST:
            set_property(
                self,
                'background',
                'selected' if self._selected else 'transparent',
            )


class AccordionHeaderWidget(QtWidgets.QFrame):
    '''Container for accordion header - holding checkbox, title, user content
    and expander button.'''

    clicked = QtCore.Signal(object)  # User header click

    @property
    def accordion(self):
        '''Return the parent accordion header lives within'''
        return self._accordion

    @property
    def collapsable(self):
        '''Return the parent accordion header lives within'''
        return self.accordion.collapsable

    @property
    def checkbox(self):
        '''Return the enable checkbox'''
        return self._checkbox

    @property
    def title_label(self):
        '''Return the title label'''
        return self._title_label

    @property
    def content(self):
        '''Return the content widget where user widgets can be added.'''
        return self._content

    @property
    def arrow(self):
        '''Return the arrow button used to collapse the accordion'''
        return self._arrow

    def __init__(self, accordion, title=None, parent=None):
        '''
        Initialize header widget

        :param accordion: The parent AccordionBaseWidget header lives within
        :param title: The default title to give header
        :param parent: The parent dialog or frame
        '''
        super(AccordionHeaderWidget, self).__init__(parent=parent)

        self._accordion = accordion

        self._checkbox = None
        self._title_label = None
        self._status = None
        self._content = None
        self._arrow = None

        self.title = title

        self.pre_build()
        self.build()

    def pre_build(self):
        self.setMinimumHeight(24)
        #    self.move(QtCore.QPoint(24, 0))
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(2, 0, 5, 0)
        self.layout().setSpacing(0)

    def build(self):
        self.layout().addWidget(
            self.init_checkbox(
                self.accordion.check_mode, self.accordion.checked
            )
        )
        self._checkbox.setVisible(
            self.accordion.check_mode != self.accordion.CHECK_MODE_NONE
        )
        self.layout().addWidget(self.init_title(self.title))
        self.layout().addWidget(self._init_content(), 10)
        self.layout().addWidget(self.init_arrow(self.accordion.collapsed))
        self._arrow.setVisible(self.collapsable)

    def init_checkbox(self, check_mode, checked):
        '''Create and return the checkable checkbox widget'''
        self._checkbox = QtWidgets.QCheckBox()
        self._checkbox.setEnabled(
            check_mode == self.accordion.CHECK_MODE_CHECKBOX
        )
        self._checkbox.setChecked(checked)
        return self._checkbox

    def init_title(self, title=None):
        '''Create and ret the title'''
        self._title_label = QtWidgets.QLabel(title or '')
        self._title_label.setObjectName('borderless')
        if not title:
            self._title_label.hide()
        return self._title_label

    def _init_content(self):
        '''Initialize header content'''
        self._content = QtWidgets.QWidget()
        self._accordion.init_header_content(
            self._content, self._accordion.collapsed
        )
        return self._content

    def init_arrow(self, collapsed):
        '''Create the arrow icon widget'''
        self._arrow = ArrowMaterialIconWidget(None)
        self.update_arrow_icon(collapsed)
        return self._arrow

    def update_arrow_icon(self, collapsed):
        '''Update the arrow icon based on collapse state'''
        if collapsed:
            icon_name = 'keyboard_arrow_down'
        else:
            icon_name = 'keyboard_arrow_up'
        self._arrow.set_icon(name=icon_name)

    def mousePressEvent(self, event):
        '''(Override)'''
        self.clicked.emit(event)
        return super(AccordionHeaderWidget, self).mousePressEvent(event)

    def set_status(self, status, message):
        '''Set status message within header, to be implemented by child'''
        pass


class ArrowMaterialIconWidget(MaterialIconWidget):
    '''Custom material icon widget for arrow, emitting event on click'''

    clicked = QtCore.Signal(object)

    def __init__(self, name, color=None, parent=None):
        super(ArrowMaterialIconWidget, self).__init__(
            name, color=color, parent=parent
        )

    def mousePressEvent(self, event):
        self.clicked.emit(event)
        return super(ArrowMaterialIconWidget, self).mousePressEvent(event)
