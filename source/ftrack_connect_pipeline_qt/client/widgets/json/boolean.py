# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.json import BaseJsonWidget


class JsonBoolean(BaseJsonWidget):
    """
        Widget representing a boolean (CheckBox)
    """
    def __init__(self, name, schema_fragment, fragment_data,
                 previous_object_data, widgetFactory, parent=None):
        super(BaseJsonWidget, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widgetFactory, parent=parent
        )
        self.checkbox = QtWidgets.QCheckBox()

        self.checkbox.setToolTip(self.description)

        self.v_layout.addWidget(self.checkbox)

    def to_json_object(self):
        return bool(self.isChecked())