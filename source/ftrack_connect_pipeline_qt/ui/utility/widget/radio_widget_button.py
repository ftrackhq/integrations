from Qt import QtWidgets, QtCore, QtGui


class RadioWidgetButton(QtWidgets.QPushButton):

    def __init__(self, label, widget, parent=None):
        super(RadioWidgetButton, self).__init__(parent)

        self.setMinimumHeight(100)  # Set minimum otherwise it will collapse the container
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setContentsMargins(20, 20, 20, 20)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        text_widget = QtWidgets.QLabel(label)
        self.layout().addWidget(text_widget)
        self.layout().addWidget(widget)

        # self.setStyleSheet("""
        #     QPushButton {
        #         background-color: rgb(50, 50, 50);
        #         border: none;
        #     }
        #
        #     QPushButton:checked {
        #         background-color: green;
        #     }
        # """)

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