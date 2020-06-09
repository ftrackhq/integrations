# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

from Qt import QtWidgets

import MaxPlus


class Viewport3dsMaxWidget(BaseOptionsWidget):
    def __init__(
            self, parent=None, session=None, data=None, name=None,
            description=None, options=None, context=None
    ):

        self.viewports = []

        for index, view in enumerate(MaxPlus.ViewportManager.Viewports):
            entry = (MaxPlus.ViewportManager.getViewportLabel(index), index)
            view_type = view.GetViewType()
            if view_type == 7:  # USER_PERSP
                self.viewports.insert(0, entry)
            else:
                self.viewports.append(entry)

        super(Viewport3dsMaxWidget, self).__init__(
            parent=parent, session=session, data=data, name=name,
            description=description, options=options, context=context
        )

    def build(self):
        super(Viewport3dsMaxWidget, self).build()
        self.nodes_cb = QtWidgets.QComboBox()
        self.layout().addWidget(self.nodes_cb)

    def post_build(self):
        super(Viewport3dsMaxWidget, self).post_build()
        if self.viewports:
            for label, index in self.viewports:
                self.nodes_cb.addItem(label, index)
            self.nodes_cb.currentIndexChanged.connect(self._process_change)
            self.set_option_result(self.nodes_cb.currentData(),
                                   'viewport_index')
        else:
            self.nodes_cb.addItem('No Viewport found.')
            self.nodes_cb.setDisabled(True)

    def _process_change(self, *args):
        self.set_option_result(self.nodes_cb.currentData(), 'viewport_index')


class Viewport3dsMaxPluginWidget(plugin.PublisherCollectorMaxWidget):
    plugin_name = 'viewport'
    widget = Viewport3dsMaxWidget


def register(api_object, **kw):
    plugin = Viewport3dsMaxPluginWidget(api_object)
    plugin.register()
