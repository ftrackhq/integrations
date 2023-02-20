# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget


class MaxFbxPublisherExporterOptionsWidget(DynamicWidget):
    '''Max FBX publisher options user input plugin widget'''

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

        super(MaxFbxPublisherExporterOptionsWidget, self).__init__(
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
            'FBXAnimation': False,
            'FBXASCII': False,
            'FBXAxisConversionMethod': [
                {'value': 'None', 'default': True},
                {'value': 'Animation'},
                {'value': 'Fbx_Root'},
            ],
            'FBXBakeAnimation': True,
            'FBXBakeFrameStart': 1,
            'FBXBakeFrameEnd': 100,
            'FBXBakeFrameStep': 1,
            'FBXBakeResampleAnimation': False,
            'FBXCameras': True,
            'FBXCAT2HIK': False,
            'FBXColladaTriangulate': False,
            'FBXColladaSingleMatrix': False,
            'FBXConvert2Tiff': True,
            'FBXConvertUnit': [
                {'value': 'mm'},
                {'value': 'cm'},
                {'value': 'dm'},
                {'value': 'm'},
                {'value': 'km'},
                {'value': 'in', 'default': True},
                {'value': 'ft'},
                {'value': 'yd'},
            ],
            'FBXEmbedTextures': False,
            'FBXExportAnimationOnly': False,
            'FBXFileVersion': [
                {'label': 'FBX 2020', 'value': 'FBX202000'},
                {'label': 'FBX 2019', 'value': 'FBX201900'},
                {'label': 'FBX 2018', 'value': 'FBX201800'},
                {'label': 'FBX 2016', 'value': 'FBX201600'},
                {'label': 'FBX 2014', 'value': 'FBX201400', 'default': True},
                {'label': 'FBX 2013', 'value': 'FBX201300'},
                {'label': 'FBX 2012', 'value': 'FBX201200'},
                {'label': 'FBX 2011', 'value': 'FBX201100'},
                {'label': 'FBX 2010', 'value': 'FBX201000'},
                {'label': 'FBX 2009', 'value': 'FBX200900'},
                {'label': 'FBX 2006', 'value': 'FBX200611'},
            ],
            'FBXFilterKeyReducer': True,
            'FBXGeomAsBone': True,
            'FBXGenerateLog': True,
            'FBXLights': True,
            'FBXLoadExportPresetFile': '',
            'FBXNormalsPerPoly': True,
            'FBXPointCache': False,
            'FBXPreserveinstances': False,
            'FBXPushSettings': '',
            'FBXRemovesinglekeys': True,
            'FBXResampling': 1.0,
            'FBXScaleFactor': 1.0,
            'FBXSelectionSet': '',
            'FBXSelectionSetExport': False,
            'FBXResetExport': False,
            'FBXShape': True,
            'FBXSkin': True,
            'FBXShowWarnings': True,
            'FBXSmoothingGroups': False,
            'FBXSplitAnimationIntoTakes': '',
            'FBXTangentSpaceExport': False,
            'FBXTriangulate': False,
            'FBXUpAxis': [
                {'value': 'y', 'default': True},
                {'value': 'z'},
            ],
            'FBXUseSceneName': False,
        }

    def get_options_group_name(self):
        '''Override'''
        return 'FBX exporter Options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        self.update(self.define_options())

        super(MaxFbxPublisherExporterOptionsWidget, self).build()


class MaxFbxPublisherExporterOptionsPluginWidget(
    plugin.MaxPublisherExporterPluginWidget
):
    plugin_name = 'max_fbx_publisher_exporter'
    widget = MaxFbxPublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxFbxPublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
