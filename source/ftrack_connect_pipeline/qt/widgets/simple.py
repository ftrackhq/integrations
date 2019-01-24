# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from QtExt import QtWidgets, QtCore
from ftrack_connect_pipeline.qt.widgets import BaseWidget


class SimpleWidget(BaseWidget):

    def extract_options(self):
        result = {}
        for label, widget in self.widget_options.items():
            result[label] = widget()

        return result

    def build_options(self, options):

        for key, value in options.items():
            option_layout = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(key)

            value_type = type(value)
            value = QtWidgets.QLineEdit(value)

            self.widget_options[key] = value.text

            option_layout.addWidget(label)
            option_layout.addWidget(value)
            self.layout().addLayout(option_layout)

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None, plugin_topic=None):
        super(SimpleWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options, plugin_topic=plugin_topic)




