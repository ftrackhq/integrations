# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

from functools import partial

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_qt.client.widgets.options.dynamic import DynamicWidget

from Qt import QtWidgets


class FbxOptionsWidget(DynamicWidget):

    def __init__(
        self, parent=None, session=None, data=None, name=None,
        description=None, options=None, context=None
    ):

        self.options_cb = {}

        super(FbxOptionsWidget, self).__init__(
            parent=parent,
            session=session, data=data, name=name,
            description=description, options=options,
            context=context)

    def build(self):
        '''build function , mostly used to create the widgets.'''
        super(FbxOptionsWidget, self).build()

        bool_options = [
            'FBXExportScaleFactor',
            'FBXExportUpAxis',
            'FBXExportFileVersion',
            'FBXExportSmoothMesh',
            'FBXExportInAscii',
            'FBXExportAnimationOnly',
            'FBXExportInstances',
            'FBXExportApplyConstantKeyReducer',
            'FBXExportBakeComplexAnimation',
            'FBXExportBakeResampleAnimation',
            'FBXExportCameras',
            'FBXExportLights',
            'FBXExportConstraints',
            'FBXExportEmbeddedTextures'
        ]

        self.option_group = QtWidgets.QGroupBox('FBX Output Options')
        self.option_group.setToolTip(self.description)

        self.option_layout = QtWidgets.QVBoxLayout()
        self.option_group.setLayout(self.option_layout)

        self.layout().addWidget(self.option_group)
        for option in bool_options:
            option_check = QtWidgets.QCheckBox(option)

            self.options_cb[option] = option_check
            self.option_layout.addWidget(option_check)

    def post_build(self):
        super(FbxOptionsWidget, self).post_build()

        for option, widget in self.options_cb.items():
            update_fn = partial(self.set_option_result, key=option)
            widget.stateChanged.connect(update_fn)


class FbxOptionsPluginWidget(plugin.PublisherOutputMayaWidget):
    plugin_name = 'fbx_options'
    widget = FbxOptionsWidget


def register(api_object, **kw):
    plugin = FbxOptionsPluginWidget(api_object)
    plugin.register()
