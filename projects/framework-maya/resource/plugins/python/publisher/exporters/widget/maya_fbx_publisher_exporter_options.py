# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_maya import plugin
from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget


class MayaFbxPublisherExporterOptionsWidget(DynamicWidget):
    '''Maya FBX publisher options user input plugin widget'''

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

        super(MayaFbxPublisherExporterOptionsWidget, self).__init__(
            parent=parent,
            session=session,
            data=data,
            name=name,
            description=description,
            options=options,
            context_id=context_id,
            asset_type_name=asset_type_name,
        )

    def define_options(self):
        '''Default renderable options for dynamic widget'''
        return {
            'FBXExportScaleFactor': 1,
            'FBXExportUpAxis': [
                {'value': 'y', 'default': True},
                {'value': 'z'},
            ],
            'FBXExportFileVersion': [
                {'label': 'FBX 2020', 'value': 'FBX202000', 'default': True},
                {'label': 'FBX 2019', 'value': 'FBX201900'},
                {'label': 'FBX 2018', 'value': 'FBX201800'},
                {'label': 'FBX 2016', 'value': 'FBX201600'},
                {'label': 'FBX 2014', 'value': 'FBX201400'},
                {'label': 'FBX 2013', 'value': 'FBX201300'},
                {'label': 'FBX 2012', 'value': 'FBX201200'},
                {'label': 'FBX 2011', 'value': 'FBX201100'},
                {'label': 'FBX 2010', 'value': 'FBX201000'},
                {'label': 'FBX 2009', 'value': 'FBX200900'},
                {'label': 'FBX 2006', 'value': 'FBX200611'},
            ],
            'FBXExportSmoothMesh': False,
            'FBXExportInAscii': False,
            'FBXExportAnimationOnly': False,
            'FBXExportInstances': False,
            'FBXExportApplyConstantKeyReducer': False,
            'FBXExportBakeComplexAnimation': False,
            'FBXExportBakeResampleAnimation': False,
            'FBXExportCameras': False,
            'FBXExportLights': True,
            'FBXExportConstraints': False,
            'FBXExportEmbeddedTextures': False,
            'FBXExportQuaternion': 'quaternion',
            'FBXExportShapes': True,
            'FBXExportSkins': True,
            'FBXExportSkeletonDefinitions': True,
            'FBXExportInputConnections': False,
            'FBXExportUseSceneName': True,
        }

    def get_options_group_name(self):
        '''Override'''
        return 'FBX exporter Options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        self.update(self.define_options())

        super(MayaFbxPublisherExporterOptionsWidget, self).build()


class MayaFbxPublisherExporterOptionsPluginWidget(
    plugin.MayaPublisherExporterPluginWidget
):
    plugin_name = 'maya_fbx_publisher_exporter'
    widget = MayaFbxPublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaFbxPublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
