# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

from Qt import QtWidgets, QtCore, QtGui
import ftrack_connect_nuke_studio.ui.widget.html_delegate


class HtmlComboBox(QtWidgets.QComboBox):
    '''Combo box that draws items with html.'''

    def __init__(self, formatter, *args, **kwargs):
        '''Initialise combo box.

        *formatter* should be a callable that accepts item data and returns a
        string of HTML to render entry with.

        .. seealso::

            :class:`ftrack_connect_nuke_studio.ui.widget.html_delegate.HtmlDelegate`

        '''
        self.format = formatter
        self._resize_occurred = False
        super(HtmlComboBox, self).__init__(*args, **kwargs)
        self.setItemDelegate(
            ftrack_connect_nuke_studio.ui.widget.html_delegate.HtmlDelegate(formatter)
        )
        self.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)

    def paintEvent(self, event):
        '''Handle paint *event*.'''
        itemData = self.itemData(self.currentIndex())

        if itemData:
            # Draw main control.
            painter = QtWidgets.QStylePainter(self)
            painter.setPen(self.palette().color(QtGui.QPalette.Text))

            option = QtWidgets.QStyleOptionComboBox()
            self.initStyleOption(option)
            painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, option)

            # Get QTextDocument from delegate to use for painting HTML text.
            delegate = self.itemDelegate()
            document = delegate.getTextDocument(
                option, self.itemData(self.currentIndex())
            )

            style = painter.style()  # QtWidgets.QApplication.style()
            paint_context = QtGui.QAbstractTextDocumentLayout.PaintContext()

            text_rectangle = style.subElementRect(
                QtWidgets.QStyle.SE_ComboBoxFocusRect, option, self
            )

            painter.save()
            painter.translate(text_rectangle.topLeft())
            painter.setClipRect(text_rectangle.translated(
                -text_rectangle.topLeft())
            )
            document.documentLayout().draw(painter, paint_context)
            painter.restore()

        else:
            super(HtmlComboBox, self).paintEvent(event)

    def resizeEvent(self, *args, **kwargs):
        '''Handle resize event.'''
        # Record a resize has occurred in order to fix issue in popup. See
        # showPopup for details.
        self._resize_occurred = True

        # Force update geometry to avoid cutting off html text.
        self.updateGeometry()

        super(HtmlComboBox, self).resizeEvent(*args, **kwargs)

    def showPopup(self, *args, **kwargs):
        '''Show popup.'''
        super(HtmlComboBox, self).showPopup(*args, **kwargs)

        # Fix bug where popup is not correctly updated after a resize (the
        # duplicate call to showPopup is necessary for clip to be updated).
        # Note: This is an imperfect solution and should be replaced if a better
        # solution can be found.
        if self._resize_occurred:
            self._resize_occurred = False
            self.view().reset()
            super(HtmlComboBox, self).showPopup(*args, **kwargs)

    def sizeHint(self):
        '''Return preferred size hint.'''
        option = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(option)

        data = self.itemData(self.currentIndex())

        # Get QTextDocument from delegate to use for calculating size hint.
        delegate = self.itemDelegate()
        document = delegate.getTextDocument(option, data)

        # Adjust the size to fix issue occurring on windows.
        size = QtCore.QSize(
            document.idealWidth(), document.size().height() + 5
        )

        return size
