from Qt import QtWidgets, QtCore, QtGui


class RadioVarticalWidgetButton(QtWidgets.QPushButton):

    def __init__(self, label, widget, parent=None):
        super(RadioVarticalWidgetButton, self).__init__(parent)

        self.setMinimumHeight(60)  # Set minimum otherwise it will collapse the container
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setContentsMargins(20, 0, 0, 20)

        self.text_label = label
        self.inner_widget = widget

        self.pre_build()
        self.build()

    def pre_build(self):
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

    def build(self):
        self.text_widget = QtWidgets.QLabel(self.text_label)
        self.text_widget.setMinimumHeight(20)

        self.inner_widget.setMinimumHeight(20)
        self.layout().setSpacing(25)
        self.layout().addWidget(self.text_widget)
        self.layout().addWidget(self.inner_widget)

    def toggle_state(self):
        if self.isChecked():
            self.text_widget.setEnabled(True)
            self.inner_widget.setEnabled(True)
            return
        self.text_widget.setEnabled(False)
        self.inner_widget.setEnabled(False)

    def paintEvent(self, event):
        # draw the widget as paintEvent normally does
        # super().paintEvent(event)

        # create a new painter on the widget
        # painter = QtGui.QPainter(self)
        # create a styleoption and init it with the button
        style = QtWidgets.QStylePainter(self)


        opt = QtWidgets.QStyleOptionButton()
        self.initStyleOption(opt)

        style.drawPrimitive(QtWidgets.QStyle.PE_IndicatorRadioButton, opt)

class RadioHorizontalWidgetButton(QtWidgets.QPushButton):

    def __init__(self, label, widget, parent=None):
        super(RadioHorizontalWidgetButton, self).__init__(parent)

        self.setMinimumHeight(60)  # Set minimum otherwise it will collapse the container
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setContentsMargins(20, 0, 0, 0)

        self.text_label = label
        self.inner_widget = widget

        self.pre_build()
        self.build()

    def pre_build(self):
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

    def build(self):
        self.text_widget = QtWidgets.QLabel(self.text_label)
        self.text_widget.setMinimumHeight(20)
        self.text_widget.setMaximumWidth(75)

        self.inner_widget.setMinimumHeight(20)
        self.layout().setSpacing(25)
        self.layout().addWidget(self.text_widget)
        self.layout().addWidget(self.inner_widget)

    def toggle_state(self):
        if self.isChecked():
            self.text_widget.setEnabled(True)
            self.inner_widget.setEnabled(True)
            return
        self.text_widget.setEnabled(False)
        self.inner_widget.setEnabled(False)

    def paintEvent(self, event):
        # draw the widget as paintEvent normally does
        # super().paintEvent(event)

        # create a new painter on the widget
        # painter = QtGui.QPainter(self)
        # create a styleoption and init it with the button
        style = QtWidgets.QStylePainter(self)


        opt = QtWidgets.QStyleOptionButton()
        self.initStyleOption(opt)

        style.drawPrimitive(QtWidgets.QStyle.PE_IndicatorRadioButton, opt)