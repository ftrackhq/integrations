# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline import constants as pipeline_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.material_icon import MaterialIconWidget
from ftrack_connect_pipeline_qt.utils import set_property

class AccordionBaseWidget(QtWidgets.QFrame):
    clicked = QtCore.Signal(object)

    SELECT_MODE_NONE = -1       # Not selectable
    #SELECT_MODE_CHECKBOX = 0    # Checkbox only
    #SELECT_MODE_CHECKBOX_AND_LIST = 1   # Checkbox and list selection
    SELECT_MODE_LIST = 0        # Only list selection mode

    CHECK_MODE_NONE = -1        # Not checkable and not showing checkbox
    CHECK_MODE_CHECKBOX = 0     # Checkable and visible
    CHECK_MODE_CHECKBOX_DISABLED = 1     # Visible but not checkable

    def on_collapse(self, collapsed):
        '''(Optional) To be overridden by child'''
        pass

    def init_header_content(self, header_layout, collapsed):
        '''To be overridden by child'''
        header_layout.addStretch()

    def init_content(self, content_layout):
        '''(Optional) To be overridden by child'''
        pass

    def update_input(self, message, status):
        '''Update the accordion input summary, should be overridden by child.'''
        raise NotImplementedError()

    @property
    def title(self):
        return self._title

    @property
    def select_mode(self):
        return self._select_mode

    @property
    def check_mode(self):
        return self._check_mode

    @property
    def checkable(self):
        return self._check_mode == self.CHECK_MODE_CHECKBOX

    @property
    def collapsed(self):
        return self._collapsed

    @property
    def selected(self):
        return self._selected

    @property
    def checked(self):
        return self._checked

    @property
    def header(self):
        return self._header

    @property
    def content(self):
        return self._content

    @property
    def session(self):
        return self._session

    def __init__(self, select_mode, check_mode, session=None, title=None, selected=False,
                 checked=True, parent=None):
        super(AccordionBaseWidget, self).__init__(parent=parent)

        self._session = session
        self._reference_widget = None
        self._collapsed = True
        self._checked = checked
        self._header = None
        self._content = None
        self._title = title
        self._widgets = {}
        self._inner_widget_status = {}

        self._select_mode = select_mode
        self._check_mode = check_mode
        self._selected = selected
        self._checked = checked

        self._input_message = 'Initializing...'
        self._input_status = False

        self.pre_build()
        self.build()
        self.post_build()


    def set_status(self, status, message):
        # TODO: Instead of run status, implement collector status
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

        content_widget = self._init_content(self._collapsed)
        main_widget.layout().addWidget(content_widget)

        self.layout().addWidget(main_widget)

    def post_build(self):
        self.update_input(self._input_message, self._input_status)
        #self.clicked.connect(self.on_click)
        if self.check_mode != self.CHECK_MODE_NONE:
            self.header.checkbox.stateChanged.connect(self.on_header_checkbox_checked)
        self.header.clicked.connect(self.on_header_clicked)
        self.header.arrow.clicked.connect(self.on_header_arrow_clicked)

    def init_header(self, title):
        self._header = AccordionHeaderWidget(self,
            title=title)
        return self._header

    def _init_content(self, collapsed):
        self._content = QtWidgets.QFrame()
        #self._content.setObjectName('bordered')
        self._content.setLayout(QtWidgets.QVBoxLayout())
        self._content.setVisible(not collapsed)

        self._content.layout().setContentsMargins(2, 2, 2, 2)
        self._content.layout().setSpacing(0)

        self.init_content(self._content.layout())

        return self._content

    def add_option_button(self, title, icon, idx):
        option_button = self._header.add_option_button(title, icon, idx)
        return option_button

    def add_widget(self, widget):
        ''' Add widget to content '''
        self._content.layout().addWidget(widget)

    def count_widgets(self):
        return self._content.layout().count()

    def get_widget_at(self, index):
        return self._content.layout().itemAt(index).widget()

    def set_selected(self, selected):
        self._selected = selected
        self.update_accordion()

    def set_checked(self, checked):
        self._checked = checked
        if self.check_mode == self.CHECK_MODE_CHECKBOX:
            return self.header.checkbox.setChecked(checked)

    def header_clicked(self):
        self._collapsed = not self._collapsed
        self.header.update_arrow_icon(int(self._collapsed))
        self.on_collapse(self.collapsed)
        self._content.setVisible(not self.collapsed)

    def enable_content(self):
        self._content.setEnabled(self.checked)

    def paint_title(self, color):
        self._header._title_label.setStyleSheet(
            "color: {}".format(color)
        )

    def set_unavailable(self):
        self.setToolTip('This component is not available in ftrack')
        if not self.checkable:
            self.paint_title("red")
            self.setToolTip(
                'This component is mandatory and is not available in ftrack'
            )
        self.set_checked(False)
        self.setEnabled(False)

    def set_default_state(self):
        self.setToolTip("")
        self.set_checked(True)
        self.setEnabled(True)

    def set_indicator(self, indication):
        set_property(self._indicator_widget, 'indicator', ('on' if indication else 'off'))

        self._indicator_widget.setVisible(True)

    def mousePressEvent(self, event):
        self.clicked.emit(event)
        self.on_click(event)
        return super(AccordionBaseWidget, self).mousePressEvent(event)

    def on_header_checkbox_checked(self):
        self._checked = self.header.checkbox.isChecked()
        self.header.title_label.setEnabled(self._checked)
        #self.checked.emit(self._checked)
        self.enable_content()

    def on_header_clicked(self, event):
        if self._select_mode == self.SELECT_MODE_NONE:
            if event.button() != QtCore.Qt.RightButton:
                self.toggle_collapsed()
        #else:
        #    # A potential selection event, leave for parent list to process
        #    self.clicked.emit(event)

    def on_header_arrow_clicked(self, event):
        if self._select_mode == self.SELECT_MODE_LIST:
            # This is the way to collapse
            self.toggle_collapsed()

    def toggle_collapsed(self):
        self._collapsed = not self._collapsed
        self.header.update_arrow_icon(int(self.collapsed))
        self.on_collapse(self.collapsed)
        self.content.setVisible(not self.collapsed)

    def on_click(self, event):
        '''Accordion were pressed overall'''
        pass

    def update_accordion(self):
        # Paint selection status
        if self._select_mode == self.SELECT_MODE_LIST:
            set_property(self, 'background', 'selected' if self._selected else 'transparent')

class AccordionHeaderWidget(QtWidgets.QFrame):
    ''' Container for accordion header - holding checkbox, title, user content
    and expander button.'''
    clicked = QtCore.Signal(object)

    @property
    def accordion(self):
        return self._accordion

    @property
    def checkbox(self):
        return self._checkbox

    @property
    def title_label(self):
        return self._title_label

    @property
    def content(self):
        ''' Return the content widget where user widgets can be added.'''
        return self._content

    @property
    def arrow(self):
        return self._arrow

    def __init__(self, accordion, title=None, parent=None):
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
        self.post_build()

    def pre_build(self):
        self.setMinimumHeight(24)
        self.move(QtCore.QPoint(24, 0))
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(15, 0, 0, 0)

    def build(self):
        self.layout().addWidget(self.init_checkbox(self.accordion.check_mode, self.accordion.checked))
        self.layout().addWidget(self.init_title(self.title))
        self.layout().addWidget(self.init_content())
        self.layout().addWidget(self.init_arrow(self.accordion.collapsed))

    def post_build(self):
        pass

    def init_checkbox(self, check_mode, checked):
        self._checkbox = QtWidgets.QCheckBox()
        self._checkbox.setEnabled(check_mode == self.accordion.CHECK_MODE_CHECKBOX)
        self._checkbox.setVisible(check_mode != self.accordion.CHECK_MODE_NONE)
        self._checkbox.setChecked(checked)
        return self._checkbox

    def init_title(self, title=None):
        self._title_label = QtWidgets.QLabel(title or '')
        self._title_label.setObjectName('borderless')
        if not title:
            self._title_label.hide()
        return self._title_label

    def init_content(self):
        self._content = QtWidgets.QWidget()
        self._content.setLayout(QtWidgets.QHBoxLayout())
        self._content.layout().setContentsMargins(0, 0, 0, 0)
        self._content.layout().setSpacing(1)
        self._accordion.init_header_content(self._content.layout(),
                self._accordion.collapsed)
        return self._content

    def update_arrow_icon(self, collapsed):
        if collapsed:
            icon_name = 'chevron-down'
        else:
            icon_name ='chevron-up'
        self._arrow.set_icon(name=icon_name)

    def init_arrow(self, collapsed):
        self._arrow = ArrowMaterialIconWidget(None)
        self.update_arrow_icon(collapsed)
        return self._arrow

    def mousePressEvent(self, event):
        self.clicked.emit(event)
        return super(AccordionHeaderWidget, self).mousePressEvent(event)

    def set_status(self, status, message):
        pass

class ArrowMaterialIconWidget(MaterialIconWidget):
    clicked = QtCore.Signal(object)

    def __init__(self, name, color=None, parent=None):
        super(ArrowMaterialIconWidget, self).__init__(name, color=color, parent=parent)

    def mousePressEvent(self, event):
        self.clicked.emit(event)
        return super(ArrowMaterialIconWidget, self).mousePressEvent(event)
