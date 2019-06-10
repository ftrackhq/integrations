# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline.client.widgets import BaseWidget
from qtpy import QtWidgets

from ftrack_connect_pipeline_3dsmax import plugin


class Viewport3dsMaxWidget(BaseWidget):
    def __init__(
            self, session=None, data=None, name=None, description=None, options=None
    ):
        import MaxPlus

        self.viewports = []

        for index, view in enumerate(MaxPlus.ViewportManager.Viewports):
            # view_type = view.GetViewType()
            # if view_type == 7:  # USER_PERSP
            self.viewports.append(
                (MaxPlus.ViewportManager.getViewportLabel(index), index)
            )

        super(Viewport3dsMaxWidget, self).__init__(
            session=session, data=data, name=name, description=description,
            options=options
        )

    def build(self):
        super(Viewport3dsMaxWidget, self).build()
        self.nodes_cb = QtWidgets.QComboBox()
        self.layout().addWidget(self.nodes_cb)
        if self.viewports:
            for label, index in self.viewports:
                self.nodes_cb.addItem(label, index)
            self.nodes_cb.currentIndexChanged.connect(
                lambda x: self.set_option_result(
                    self.notes_cb.currentData(), key='viewport_index'
                )
            )
            self.set_option_result(self.nodes_cb.currentData(), 'viewport_index')
        else:
            self.nodes_cb.addItem('No Viewport found.')
            self.nodes_cb.setDisabled(True)


class Viewport3dsMaxPlugin(plugin.CollectorMaxWidget):
    plugin_name = 'viewport'

    def run(self, data=None, name=None, description=None, options=None):
        return Viewport3dsMaxWidget(
            session=self.session, data=data, name=name,
            description=description, options=options
        )


def register(api_object, **kw):
    plugin = Viewport3dsMaxPlugin(api_object)
    plugin.register()
