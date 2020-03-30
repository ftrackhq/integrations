import logging
from qtpy import QtWidgets, QtCore, QtGui
from ftrack_connect_pipeline import constants


class AccordionWidget(QtWidgets.QWidget):
    def __init__(self, parent=None, title=None):
        super(AccordionWidget, self).__init__(parent=parent)

        self._reference_widget = None
        self._is_collasped = True
        self._title_frame = None
        self._content, self._content_layout = (None, None)
        self._title = title

        self.pre_build()
        self.build()
        self.post_build()

    def get_option_results(self):
        return self._reference_widget.get_option_results()

    def set_status(self, status, message):
        self._title_frame._status.set_status(status, message)

    def pre_build(self):
        self._main_v_layout = QtWidgets.QVBoxLayout(self)
        self._main_v_layout.setAlignment(QtCore.Qt.AlignTop)
        self._main_v_layout.setContentsMargins(0, 0, 0, 0)

    def build(self):
        title_widget = self.initTitleFrame(self._title, self._is_collasped)
        self._main_v_layout.addWidget(title_widget)

        content_widget = self.initContent(self._is_collasped)
        self._main_v_layout.addWidget(content_widget)

    def post_build(self):
        self.initCollapsable()

    def initTitleFrame(self, title, collapsed):
        self._title_frame = AccordionTitleWidget(
            title=title, collapsed=collapsed)

        return self._title_frame

    def initContent(self, collapsed):
        self._content = QtWidgets.QWidget()
        self._content_layout = QtWidgets.QVBoxLayout()

        self._content.setLayout(self._content_layout)
        self._content.setVisible(not collapsed)

        return self._content

    def addWidget(self, widget):
        self._content_layout.addWidget(widget)
        self._reference_widget = widget
        widget.status_updated.connect(self.set_status)

    def initCollapsable(self):
        self._title_frame.clicked.connect(self.toggleCollapsed)

    def toggleCollapsed(self):
        self._content.setVisible(self._is_collasped)
        self._is_collasped = not self._is_collasped
        self._title_frame._arrow.setArrow(int(self._is_collasped))


class AccordionTitleWidget(QtWidgets.QFrame):
    clicked = QtCore.Signal()

    def __init__(self, parent=None, title="", collapsed=False):
        super(AccordionTitleWidget, self).__init__(parent=parent)

        self.setMinimumHeight(24)
        self.move(QtCore.QPoint(24, 0))
        # self.setStyleSheet("border:1px solid rgb(41, 41, 41); ")

        self._hlayout = QtWidgets.QHBoxLayout(self)
        self._hlayout.setContentsMargins(0, 0, 0, 0)
        self._hlayout.setSpacing(0)

        self._arrow = None
        self._title = None
        self._status = None

        self._hlayout.addWidget(self.initTitle(title))
        self._hlayout.addWidget(self.initStatus())
        self._hlayout.addWidget(self.initArrow(collapsed))

    def initStatus(self):
        self._status = Status()
        return self._status

    def initArrow(self, collapsed):
        self._arrow = Arrow(collapsed=collapsed)
        self._arrow.setStyleSheet("border:0px")

        return self._arrow

    def initTitle(self, title=None):
        self._title = QtWidgets.QLabel(title)
        self._title.setMinimumHeight(24)
        self._title.move(QtCore.QPoint(24, 0))
        self._title.setStyleSheet("border:0px")

        return self._title

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
        self.setArrow(int(collapsed))

    def setArrow(self, arrow_dir):
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