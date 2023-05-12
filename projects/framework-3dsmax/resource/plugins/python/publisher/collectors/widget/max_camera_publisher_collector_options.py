# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
from functools import partial

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget

from Qt import QtWidgets

import ftrack_api


class MaxCameraPublisherCollectorOptionsWidget(BaseOptionsWidget):
    '''Max camera collector widget plugin'''

    # Run fetch function on widget initialization
    auto_fetch_on_init = True

    _cameras = []

    @property
    def cameras(self):
        return self._cameras

    @cameras.setter
    def cameras(self, cameras):
        self._cameras = cameras
        self.cameras_cb.clear()
        if not self.cameras:
            self.cameras_cb.setDisabled(True)
            self.cameras_cb.addItem('No suitable cameras found.')
        else:
            selected_index = 0
            for index, item in enumerate(self.cameras):
                self.cameras_cb.addItem(item)
                if (
                    self._camera_name
                    and item.lower() == self._camera_name.lower()
                ):
                    selected_index = index
            if selected_index > -1:
                self.cameras_cb.setCurrentIndex(selected_index)
            self.set_option_result(
                self.cameras_cb.currentText(), key='camera_name'
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

        self._cameras = []
        self._camera_name = options.get('camera_name')
        super(MaxCameraPublisherCollectorOptionsWidget, self).__init__(
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
        super(MaxCameraPublisherCollectorOptionsWidget, self).build()
        self.cameras_cb = QtWidgets.QComboBox()
        self.cameras_cb.setToolTip(self.description)
        self.layout().addWidget(self.cameras_cb)

    def _on_camera_selected(self, unused_text):
        self.set_option_result(
            self.cameras_cb.currentText(), key='camera_name'
        )

    def post_build(self):
        super(MaxCameraPublisherCollectorOptionsWidget, self).post_build()
        update_fn = partial(self.set_option_result, key='camera_name')
        self.cameras_cb.currentTextChanged.connect(update_fn)
        if self.cameras:
            self.set_option_result(
                self.cameras_cb.currentText(), key='camera_name'
            )

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.cameras = result

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        message = ''
        status = False
        num_objects = 1 if self.cameras_cb.isEnabled() else 0
        if num_objects > 0:
            message = '{} camera{} selected'.format(
                num_objects, 's' if num_objects > 1 else ''
            )
            status = True
        self.inputChanged.emit(
            {
                'status': status,
                'message': message,
            }
        )


class MaxCameraPublisherCollectorPluginWidget(
    plugin.MaxPublisherCollectorPluginWidget
):
    plugin_name = 'max_camera_publisher_collector'
    widget = MaxCameraPublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxCameraPublisherCollectorPluginWidget(api_object)
    plugin.register()
