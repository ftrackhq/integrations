# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

from Qt import QtWidgets, QtCore, QtGui

from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline import constants as pipeline_constants
from ftrack_connect_pipeline_qt.ui.utility.widget.material_icon import MaterialIconWidget


class AccordionBaseWidget(QtWidgets.QFrame):

    def on_collapse(self, collapsed):
        '''To be overridden by child'''
        pass

    def init_header_content(self, header_layout, collapsed):
        '''To be overridden by child'''
        header_layout.addStretch()

    def init_content(self, content_layout):
        '''To be overridden by child'''
        pass

    def update_input(self, message, status):
        '''Update the accordion input summary, should be overridden by child.'''
        raise NotImplementedError()

    @property
    def title(self):
        return self._title

    @property
    def collapsed(self):
        return self._collapsed

    @property
    def checked(self):
        return self._header.checkbox.isChecked()

    @property
    def header(self):
        return self._header

    @property
    def content(self):
        return self._content

    @property
    def session(self):
        return self._session

    def __init__(self, session=None, title=None, checkable=False, checked=True, parent=None):
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
        self.checkable = checkable

        self._input_message = 'Initializing...'
        self._input_status = False

        self.pre_build()
        self.build()
        self.post_build()

        #self.setStyleSheet('background-color: red;')

    def set_status(self, status, message):
        # TODO: Instead of run status, implement collector status
        self._header.set_status(status, message)

    def pre_build(self):
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(1)

    def build(self):
        title_widget = self.init_header(self._title, self._collapsed)
        self.layout().addWidget(title_widget)

        content_widget = self._init_content(self._collapsed)
        self.layout().addWidget(content_widget)

    def post_build(self):
        self.init_collapsable()
        self.update_input(self._input_message, self._input_status)

    def init_header(self, title, collapsed):
        self._header = AccordionHeaderWidget(self,
            title=title, collapsed=collapsed, checkable=self.checkable, checked=self._checked)
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

    def init_collapsable(self):
        self._header.clicked.connect(self.toggle_collapsed)
        self._header.checked.connect(self.enable_content)

    def is_checked(self):
        if self._header.checkable:
            return self._header.checkbox.isChecked()
        return True

    def set_checked(self, checked):
        if self._header.checkable:
            return self._header.checkbox.setChecked(checked)

    def toggle_collapsed(self):
        self._collapsed = not self._collapsed
        self._header.update_arrow_icon(int(self._collapsed))
        self.on_collapse(self.collapsed)
        self._content.setVisible(not self.collapsed)

    def enable_content(self, check_enabled):
        self._content.setEnabled(check_enabled)

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
        if not self.checkable:
            self._header._title_label.setStyleSheet("")
        self.set_checked(True)
        self.setEnabled(True)


class AccordionHeaderWidget(QtWidgets.QFrame):
    ''' Container for accordion header - holding checkbox, title, user content
    and expander button.'''
    clicked = QtCore.Signal()
    checked = QtCore.Signal(object)

    @property
    def checkbox(self):
        return self._checkbox

    @property
    def content(self):
        ''' Return the content widget where user widgets can be added.'''
        return self._content

    def __init__(self, accordion, title=None, collapsed=False,
                 checkable=False, checked=True, parent=None):
        super(AccordionHeaderWidget, self).__init__(parent=parent)

        self._accordion = accordion

        self._checkbox = None
        self._title_label = None
        self._status = None
        self._content = None
        self._arrow = None

        self.title = title
        self.initial_collapse = collapsed
        self.checkable = checkable
        self._checked = checked

        self.pre_build()
        self.build()
        self.post_build()

    def pre_build(self):
        self.setMinimumHeight(24)
        self.move(QtCore.QPoint(24, 0))
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(15, 0, 0, 0)

    def build(self):
        self.layout().addWidget(self.init_checkbox(self._checked, self.checkable))
        self.layout().addWidget(self.init_title(self.title))
        self.layout().addWidget(self.init_content())
        self.layout().addWidget(self.init_arrow(self.initial_collapse))

    def post_build(self):
        if self.checkbox:
            self._checkbox.stateChanged.connect(self.enable_content)

    def init_checkbox(self, checked, enabled):
        self._checkbox = QtWidgets.QCheckBox()
        self._checkbox.setChecked(checked)
        self._checkbox.setEnabled(enabled)
        return self._checkbox

    def init_title(self, title=None):
        self._title_label = QtWidgets.QLabel(title or '')
        self._title_label.setStyleSheet("border:0px")
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
        self._arrow = MaterialIconWidget(None)
        self.update_arrow_icon(collapsed)
        return self._arrow

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            return
        self.clicked.emit()
        return super(AccordionHeaderWidget, self).mousePressEvent(event)

    def enable_content(self, check_enabled):
        self._title_label.setEnabled(check_enabled)
        self.checked.emit(check_enabled)

    def set_status(self, status, message):
        pass
