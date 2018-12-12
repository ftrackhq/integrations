import ftrack_api
from QtExt import QtWidgets, QtCore


class SimpleWidget(QtWidgets.QWidget):
    status_changed = QtCore.Signal(object)

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

    def __init__(self, parent=None, session=None, data=None, name=None, description=None, options=None, call_topic=None):
        super(SimpleWidget, self).__init__(parent=parent)
        self.session = session
        self.call_topic = call_topic
        self.widget_options = {}
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        name = QtWidgets.QLabel(name)
        name.setToolTip(description)

        layout.addWidget(name)
        self.build_options(options)


