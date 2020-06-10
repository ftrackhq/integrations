import logging

from functools import partial

from Qt import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline_qt import constants
from ftrack_connect_pipeline import constants as pipeline_constants
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget


class AccordionWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, title=None):
        super(AccordionWidget, self).__init__(parent=parent)

        self._reference_widget = None
        self._is_collasped = True
        self._title_frame = None
        self._content, self._content_layout = (None, None)
        self._title = title
        self._widgets = {}
        self._inner_widget_status = {}

        self.pre_build()
        self.build()
        self.post_build()

    def set_status(self, status, message):
        self._title_frame._status.set_status(status, message)

    def pre_build(self):
        self._main_v_layout = QtWidgets.QVBoxLayout()
        self._main_v_layout.setAlignment(QtCore.Qt.AlignTop)
        self._main_v_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._main_v_layout)

    def build(self):
        title_widget = self.init_title_frame(self._title, self._is_collasped)
        self._main_v_layout.addWidget(title_widget)

        content_widget = self.init_content(self._is_collasped)
        self._main_v_layout.addWidget(content_widget)

    def post_build(self):
        self.init_collapsable()

    def init_title_frame(self, title, collapsed):
        self._title_frame = AccordionTitleWidget(
            title=title, collapsed=collapsed)
        return self._title_frame

    def init_content(self, collapsed):
        self._content = QtWidgets.QWidget()
        self._content_layout = QtWidgets.QVBoxLayout()

        self._content.setLayout(self._content_layout)
        self._content.setVisible(not collapsed)

        return self._content

    def update_inner_status(self, inner_widget, data):
        status, message = data

        self._inner_widget_status[inner_widget] = status

        all_bool_status = [
            pipeline_constants.status_bool_mapping[_status]
            for _status in list(self._inner_widget_status.values())
        ]
        if all(all_bool_status):
            self.set_status(constants.SUCCESS_STATUS, None)
        else:
            if constants.RUNNING_STATUS in list(self._inner_widget_status.values()):
                self.set_status(constants.RUNNING_STATUS, None)
            else:
                self.set_status(constants.ERROR_STATUS, None)

    def add_widget(self, widget):
        self._content_layout.addWidget(widget)
        self._connect_inner_widgets(widget)

    def _connect_inner_widgets(self, widget):
        inner_widgets = widget.findChildren(BaseOptionsWidget)
        self._widgets[widget] = inner_widgets
        for inner_widget in inner_widgets:
            inner_widget.status_updated.connect(
                partial(self.update_inner_status, inner_widget)
            )

    def count_widgets(self):
        return self._content_layout.count()

    def get_witget_at(self, index):
        return self._content_layout.itemAt(index).widget()

    def init_collapsable(self):
        self._title_frame.clicked.connect(self.toggle_collapsed)

    def toggle_collapsed(self):
        self._content.setVisible(self._is_collasped)
        self._is_collasped = not self._is_collasped
        self._title_frame._arrow.set_arrow(int(self._is_collasped))


class AccordionTitleWidget(QtWidgets.QFrame):
    clicked = QtCore.Signal()

    def __init__(self, parent=None, title="", collapsed=False, checkable=False):
        super(AccordionTitleWidget, self).__init__(parent=parent)

        self._arrow = None
        self._title_label = None
        self._status = None
        self._checkbox = None

        self.title = title
        self.initial_collapse = collapsed
        self.checkable = checkable


        self.pre_build()
        self.build()

    def pre_build(self):
        self.setMinimumHeight(24)
        self.move(QtCore.QPoint(24, 0))
        self._hlayout = QtWidgets.QHBoxLayout(self)
        self._hlayout.setContentsMargins(0, 0, 0, 0)

    def build(self):
        if self.checkable:
            self._hlayout.addWidget(self.init_checkbox(True))
        self._hlayout.addWidget(self.init_title(self.title))
        self._hlayout.addStretch()
        self._hlayout.addWidget(self.init_arrow(self.initial_collapse))
        self._hlayout.addWidget(self.init_status())

    def init_status(self):
        self._status = Status()
        return self._status

    def init_arrow(self, collapsed):
        self._arrow = Arrow(collapsed=collapsed)
        self._arrow.setStyleSheet("border:0px")

        return self._arrow

    def init_title(self, title=None):
        self._title_label = QtWidgets.QLabel(title)
        self._title_label.setStyleSheet("border:0px")

        return self._title_label

    def init_checkbox(self, checked):
        self._checkbox = QtWidgets.QCheckBox()
        self._checkbox.setChecked(checked)

        return self._checkbox

    def mousePressEvent(self, event):
        self.clicked.emit()
        return super(AccordionTitleWidget, self).mousePressEvent(event)


class Status(QtWidgets.QLabel):
    status_icons = constants.icons.status_icons

    def __init__(self, parent=None):
        super(Status, self).__init__(parent=parent)
        icon = self.status_icons[constants.DEFAULT_STATUS]
        self.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.setPixmap(icon)

    def set_status(self, status, message=None):
        icon = self.status_icons[status]
        self.setPixmap(icon)
        if message:
            self.setToolTip(str(message))


class Arrow(QtWidgets.QFrame):
    def __init__(self, parent=None, collapsed=False):
        super(Arrow, self).__init__(parent=parent)

        self.setMinimumSize(24, 24)
        self.setMaximumSize(24, 24)

        # horizontal == 0
        self._arrow_horizontal = QtGui.QPolygonF().fromList(
            [
                QtCore.QPointF(7.0, 8.0),
                QtCore.QPointF(17.0, 8.0),
                QtCore.QPointF(12.0, 13.0)
            ]
        )
        # vertical == 1
        self._arrow_vertical = QtGui.QPolygonF().fromList(
            [
                QtCore.QPointF(8.0, 7.0),
                QtCore.QPointF(13.0, 12.0),
                QtCore.QPointF(8.0, 17.0)
            ]
        )
        # arrow
        self._arrow = None
        self.set_arrow(int(collapsed))

    def set_arrow(self, arrow_dir):
        if arrow_dir:
            self._arrow = self._arrow_vertical
        else:
            self._arrow = self._arrow_horizontal

    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setBrush(QtGui.QColor(192, 192, 192))
        painter.setPen(QtGui.QColor(64, 64, 64))
        painter.drawPolygon(self._arrow)
        painter.end()