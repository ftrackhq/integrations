# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


from Qt import QtCore, QtWidgets
from ftrack_connect_pipeline_qt.client.widgets.json import BaseJsonWidget


class ComponentsArray(BaseJsonWidget):

    def __init__(self, name, schema_fragment, fragment_data,
                 previous_object_data, widgetFactory, parent=None):
        super(ComponentsArray, self).__init__(
            name, schema_fragment, fragment_data, previous_object_data,
            widgetFactory, parent=parent
        )
        self.tabWidget = QtWidgets.QTabWidget()

        if "items" in self.schema_fragment and self.fragment_data:
            for data in self.fragment_data:
                newTabWidget = QtWidgets.QWidget()
                widgetLayout = QtWidgets.QVBoxLayout()
                obj = self.widget_factory.create_widget(
                    data['name'], self.schema_fragment['items'], data,
                    self.previous_object_data)
                widgetLayout.addWidget(obj)
                newTabWidget.setLayout(widgetLayout)
                self.tabWidget.addTab(newTabWidget, data["name"])

        self.v_layout.addWidget(self.tabWidget)
        self.layout().setContentsMargins(0, 0, 0, 0)