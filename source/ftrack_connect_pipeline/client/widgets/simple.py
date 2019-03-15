# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from QtExt import QtWidgets
from ftrack_connect_pipeline.client.widgets import BaseWidget


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

            value = QtWidgets.QLineEdit(str(value))

            self.widget_options[key] = value.text

            option_layout.addWidget(label)
            option_layout.addWidget(value)
            self.layout().addLayout(option_layout)

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None):
        super(SimpleWidget, self).__init__(parent=parent, session=session, data=data, name=name, description=description, options=options)




