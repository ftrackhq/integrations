from Qt import QtWidgets, QtCore, QtGui


class RadioWidgetButton(QtWidgets.QPushButton):

    def __init__(self, label, widget, parent=None):
        super(RadioWidgetButton, self).__init__(parent)

        self.setMinimumHeight(60)  # Set minimum otherwise it will collapse the container
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setContentsMargins(20, 0, 0, 20)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.text_widget = QtWidgets.QLabel(label)
        self.text_widget.setMinimumHeight(20)

        self.inner_widget = widget

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