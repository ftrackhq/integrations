# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import ftrack_api

from ftrack_connect_pipeline_3dsmax import plugin
from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget


class MaxFbxLoaderImporterOptionsWidget(DynamicWidget):
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

        super(MaxFbxLoaderImporterOptionsWidget, self).__init__(
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
            'FBXAnimation': True,
            'FBXAxisConversion': False,
            'FBXBakeAnimationLayers': True,
            'FBXCameras': True,
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
            'FBXFillTimeline': True,
            'FBXFilterKeyReducer': True,
            'FBXFilterKeySync': True,
            'FBXGenerateLog': True,
            'FBXImportBoneAsDummy': True,
            'FBXKeepFrameRate': False,
            'FBXLights': True,
            'FBXLoadImportPresetFile': '',
            'FBXMarkers': False,
            'FBXMode': [
                {
                    'label': 'Add to new scene',
                    'value': 'create',
                    'default': True,
                },
                {'label': 'Exclusive Merge', 'value': 'exmerge'},
                {'label': 'Merge, Update animation', 'value': 'merge'},
            ],
            'FBXPopSettings': '',
            'FBXPushSettings': '',
            'FBXPointCache': True,
            'FBXPostSamplingKeyReducer': '',
            'FBXResampling': 1.0,
            'FBXResetImport': False,
            'FBXScaleConversion': True,
            'FBXScaleFactor': 1.0,
            'FBXShape': True,
            'FBXSkin': True,
            'FBXSmoothingGroups': False,
            'FBXTakeCount': 1,
            'FBXTakeIndex': 1,
            'FBXUpAxis': [
                {'value': 'y', 'default': True},
                {'value': 'z'},
            ],
        }

    def get_options_group_name(self):
        '''Override'''
        return 'FBX exporter Options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        self.update(self.define_options())

        super(MaxFbxLoaderImporterOptionsWidget, self).build()


class MaxFbxLoaderImporterOptionsPluginWidget(
    plugin.MaxLoaderImporterPluginWidget
):
    plugin_name = 'max_fbx_loader_importer'
    widget = MaxFbxLoaderImporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MaxFbxLoaderImporterOptionsPluginWidget(api_object)
    plugin.register()
