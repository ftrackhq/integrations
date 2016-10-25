# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
from QtExt import QtGui, QtCore, QtWidgets


class FlowLayout(QtWidgets.QLayout):
    '''PyQt4 Example modified to work with a scrollable parent.

    Based on the implementation: https://github.com/cgdougm/PyQtFlowLayout
    '''

    def __init__(self, parent=None, spacing=-1):
        '''Initialize layout'''
        super(FlowLayout, self).__init__(parent)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        w = self.geometry().width()
        h = self.doLayout(QtCore.QRect(0, 0, w, 0), True)
        return QtCore.QSize(w, h)

    def doLayout(self, rect, testOnly=False):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()

            spaceX = self.spacing() + wid.style().layoutSpacing(
                QtWidgets.QSizePolicy.PushButton,
                QtWidgets.QSizePolicy.PushButton,
                QtCore.Qt.Horizontal
            )

            spaceY = self.spacing() + wid.style().layoutSpacing(
                QtWidgets.QSizePolicy.PushButton,
                QtWidgets.QSizePolicy.PushButton,
                QtCore.Qt.Vertical
            )

            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(
                    QtCore.QRect(
                        QtCore.QPoint(x, y), item.sizeHint()
                    )
                )

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()


class ResizeScrollArea(QtWidgets.QScrollArea):
    '''A QScrollArea that propagates the resizing to any FlowLayout children.'''

    def __init(self, parent=None):
        super(ResizeScrollArea, self).__init__(parent)

    def resizeEvent(self, event):
        wrapper = self.findChild(QtWidgets.QWidget)
        flow = wrapper.findChild(FlowLayout)

        if wrapper and flow:
            width = self.viewport().width()
            height = flow.heightForWidth(width)
            size = QtCore.QSize(width, height)
            point = self.viewport().rect().topLeft()
            flow.setGeometry(QtCore.QRect(point, size))
            self.viewport().update()

        super(ResizeScrollArea, self).resizeEvent(event)


class ScrollingFlowWidget(QtWidgets.QWidget):
    '''A resizable and scrollable widget that uses a flow layout.

    Use its addWidget() method to flow children into it.
    '''

    def __init__(self, parent=None):
        super(ScrollingFlowWidget, self).__init__(parent)
        grid = QtWidgets.QGridLayout(self)
        scroll = ResizeScrollArea(parent)
        self._wrapper = QtWidgets.QWidget(scroll)
        self.flowLayout = FlowLayout(self._wrapper)
        self._wrapper.setLayout(self.flowLayout)
        scroll.setWidget(self._wrapper)
        scroll.setWidgetResizable(True)
        grid.addWidget(scroll)

    def addWidget(self, widget):
        self.flowLayout.addWidget(widget)
        widget.setParent(self._wrapper)
