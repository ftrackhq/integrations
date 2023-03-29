# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack

from functools import partial

from ftrack_connect_pipeline_{{cookiecutter.host_type}} import plugin
from ftrack_connect_pipeline_qt.plugin.widget import BaseOptionsWidget

from Qt import QtWidgets

import ftrack_api


class {{cookiecutter.host_type_capitalized}}CameraPublisherCollectorOptionsWidget(BaseOptionsWidget):
    ''' {{cookiecutter.host_type_capitalized}} camera collector widget plugin'''
    # Run fetch function on widget initialization
    auto_fetch_on_init = True

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

        self.{{cookiecutter.host_type}}_cameras = []
        super({{cookiecutter.host_type_capitalized}}CameraPublisherCollectorOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        self.{{cookiecutter.host_type}}_cameras = result
        if self.{{cookiecutter.host_type}}_cameras:
            self.cameras.setDisabled(False)
        else:
            self.cameras.setDisabled(True)
        self.cameras.clear()
        self.cameras.addItems(result)

    def build(self):
        '''build function , mostly used to create the widgets.'''
        super({{cookiecutter.host_type_capitalized}}CameraPublisherCollectorOptionsWidget, self).build()
        self.cameras = QtWidgets.QComboBox()
        self.cameras.setToolTip(self.description)
        self.layout().addWidget(self.cameras)

        if self.options.get('camera_name'):
            self.{{cookiecutter.host_type}}_cameras.append(self.options.get('camera_name'))

        if not self.{{cookiecutter.host_type}}_cameras:
            self.cameras.setDisabled(True)
            self.cameras.addItem('No suitable cameras found.')
        else:
            self.cameras.addItems(self.{{cookiecutter.host_type}}_cameras)

    def post_build(self):
        super({{cookiecutter.host_type_capitalized}}CameraPublisherCollectorOptionsWidget, self).post_build()
        update_fn = partial(self.set_option_result, key='camera_name')

        self.cameras.currentTextChanged.connect(update_fn)
        if self.{{cookiecutter.host_type}}_cameras:
            self.set_option_result(
                self.cameras.currentText(), key='camera_name'
            )

    def report_input(self):
        '''(Override) Amount of collected objects has changed, notify parent(s)'''
        message = ''
        status = False
        num_objects = 1 if self.cameras.isEnabled() else 0
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


class {{cookiecutter.host_type_capitalized}}CameraPublisherCollectorPluginWidget(
    plugin.{{cookiecutter.host_type_capitalized}}PublisherCollectorPluginWidget
):
    plugin_name = '{{cookiecutter.host_type}}_camera_publisher_collector'
    widget = {{cookiecutter.host_type_capitalized}}CameraPublisherCollectorOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = {{cookiecutter.host_type_capitalized}}CameraPublisherCollectorPluginWidget(api_object)
    plugin.register()
