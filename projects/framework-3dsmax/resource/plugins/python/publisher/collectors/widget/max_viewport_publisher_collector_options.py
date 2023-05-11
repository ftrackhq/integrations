# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget

from Qt import QtWidgets

import ftrack_api


class MaxViewportPublisherCollectorOptionsWidget(BaseOptionsWidget):
    '''Max viewport collector widget plugin'''

    # Run fetch function on widget initialization
    auto_fetch_on_init = True

    _viewports = []

    @property
    def viewports(self):
        return self._viewports

    @viewports.setter
    def viewports(self, viewports):
        self._viewports = viewports
        self.viewports_cb.clear()
        if not self.viewports:
            self.viewports_cb.setDisabled(True)
            self.viewports_cb.addItem('No suitable viewports found.')
        else:
            selected_index = 0
            for index, item in enumerate(self.viewports):
                self.viewports_cb.addItem(item[0], item[1])
                if (
                    self._viewport_name
                    and item[0].lower() == self._viewport_name.lower()
                ):
                    selected_index = index
                if self._viewport_index and item[1] == self._viewport_index:
                    selected_index = index
            if selected_index > -1:
                self.viewports_cb.setCurrentIndex(selected_index)
            self.set_option_result(
                self.viewports_cb.currentData(), key='viewport_index'
            )

    def __init__(
        self,
        parent=None,
        session=None,
        data=None,
        name=None,
        description=None,
        options=None,
        context_id=None,
        asset_type_name=None,
    ):

        self._viewports = []
        self._viewport_name = options.get('viewport_name')
        self._viewport_index = options.get('viewport_index')
        super(MaxViewportPublisherCollectorOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def build(self):
        '''build function , mostly used to create the widgets.'''
        super(MaxViewportPublisherCollectorOptionsWidget, self).build()
        self.viewports_cb = QtWidgets.QComboBox()
        self.viewports_cb.setToolTip(self.description)
        self.layout().addWidget(self.viewports_cb)

    def _on_viewport_selected(self, unused_text):
        self.set_option_result(
            self.viewports_cb.currentData(), key='viewport_index'
        )

    def post_build(self):
        super(MaxViewportPublisherCollectorOptionsWidget, self).post_build()
        self.viewports_cb.currentTextChanged.connect(
            self._on_viewport_selected
        )
        if self.viewports:
            self.set_option_result(
                self.viewports_cb.currentText(), key='viewport_name'
            )

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.viewports = result

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        message = ''
        status = False
        num_objects = 1 if self.viewports_cb.isEnabled() else 0
        if num_objects > 0:
            message = '{} viewport{} selected'.format(
                num_objects, 's' if num_objects > 1 else ''
            )
            status = True
        self.inputChanged.emit(
            {
                'status': status,
                'message': message,
            }
        )


class MaxViewportPublisherCollectorPluginWidget(
    plugin.MaxPublisherCollectorPluginWidget
):
    plugin_name = 'max_viewport_publisher_collector'
    widget = MaxViewportPublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxViewportPublisherCollectorPluginWidget(api_object)
    plugin.register()
