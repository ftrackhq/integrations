# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from functools import partial

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_qt.client.widgets.options import BaseOptionsWidget

from Qt import QtWidgets

import maya.cmds as mcd


class CameraCollectorWidget(BaseOptionsWidget):

    def __init__(
        self, parent=None, session=None, data=None, name=None,
        description=None, options=None, context=None
    ):

        # list all perspective camera
        self.maya_cameras = mcd.listCameras(p=True)

        super(CameraCollectorWidget, self).__init__(
            parent=parent,
            session=session, data=data, name=name,
            description=description, options=options,
            context=context)

    def build(self):
        '''build function , mostly used to create the widgets.'''
        super(CameraCollectorWidget, self).build()
        self.cameras = QtWidgets.QComboBox()
        self.cameras.setToolTip(self.description)
        self.layout().addWidget(self.cameras)

        if not self.maya_cameras:
            self.cameras.setDisabled(True)
            self.cameras.addItem('No Suitable Cameras found.')
        else:
            self.cameras.addItems(self.maya_cameras)

    def post_build(self):
        super(CameraCollectorWidget, self).post_build()
        update_fn = partial(self.set_option_result, key='camera_name')

        self.cameras.editTextChanged.connect(update_fn)
        self.set_option_result(self.maya_cameras[0], key='camera_name')


class CameraCollectorPluginWidget(plugin.CollectorMayaWidget):
    plugin_name = 'camera'
    widget = CameraCollectorWidget


def register(api_object, **kw):
    plugin = CameraCollectorPluginWidget(api_object)
    plugin.register()
