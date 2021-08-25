# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

import logging
from ftrack_connect_pipeline_qt.client.widgets.experimental import BaseUIWidget
from Qt import QtGui, QtCore, QtWidgets

from Qt import QtWidgets, QtCore, QtGui


class ComponentButton(QtWidgets.QPushButton):

    def __init__(self, component_name, status, parent=None):
        super(ComponentButton, self).__init__(parent)

        self.setMinimumHeight(100)  # Set minimum otherwise it will collapse the container
        # self.setCheckable(True)
        # self.setAutoExclusive(True)
        self.setContentsMargins(20, 20, 20, 20)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        text_widget = QtWidgets.QLabel(component_name)
        self.layout().addWidget(text_widget)
        self.status = QtWidgets.QLabel(status)
        self.layout().addWidget(self.status)

    def update_status(self, status):
        self.status.text(status)

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

    # def paintEvent(self, event):
    #     # draw the widget as paintEvent normally does
    #     # super().paintEvent(event)
    #
    #     # create a new painter on the widget
    #     # painter = QtGui.QPainter(self)
    #     # create a styleoption and init it with the button
    #     style = QtWidgets.QStylePainter(self)
    #
    #
    #     opt = QtWidgets.QStyleOptionButton()
    #     self.initStyleOption(opt)
    #
    #     style.drawPrimitive(QtWidgets.QStyle.PE_IndicatorRadioButton, opt)



class ProgressWidget(BaseUIWidget):
    '''Widget representation of a boolean'''
    component_widgets = {}
    # on_update_status = QtCore.Signal(object)

    # def _set_internal_status(self, data):
    #     '''set the status icon with the provided *data*'''
    #     status, message = data
    #     icon = self.status_icons[status]
    #     self._status_icon.setPixmap(icon)
    #     self._status_icon.setToolTip(str(message))

    def __init__(self, name, fragment_data, parent=None):
        '''Initialise JsonBoolean with *name*, *schema_fragment*,
        *fragment_data*, *previous_object_data*, *widget_factory*, *parent*'''
        super(ProgressWidget, self).__init__(
            name, fragment_data, parent=parent
        )

    def build(self):
        self._widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()
        self.widget.setLayout(main_layout)

    # def post_build(self):
    #     '''post build function , mostly used connect widgets events.'''
    #     self.on_update_status.connect(self._set_internal_status)

    def add_component(self, type_name, step_name):
        id_name = "{}.{}".format(type_name, step_name)
        component_name = step_name
        component_button = ComponentButton(component_name, "Not started")
        self.component_widgets[id_name] = component_button
        self.widget.layout().addWidget(component_button)

    def update_component_status(self, type_name, step_name, status):
        id_name = "{}.{}".format(type_name, step_name)
        self.component_widgets[id_name].update_status(status)