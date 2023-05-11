# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_connect_pipeline_houdini import plugin
from ftrack_connect_pipeline_qt.plugin.widget.dynamic import DynamicWidget

import ftrack_api


class HoudiniFbxPublisherExporterOptionsWidget(DynamicWidget):

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
        super(HoudiniFbxPublisherExporterOptionsWidget, self).__init__(
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
            'FBXASCII': True,
            "FBXValidFrameRange": [
                {"label": "Current frame", "value": 0},
                {"label": "Render frame range", "value": 1},
                {"label": "Render frame range only (strict)", "value": 2},
            ],
            "FBXFrameRangeStart": "1.0",
            "FBXFrameRangeEnd": "100.0",
            "FBXFrameRangeBy": "1.0",
            "FBXTake": "_current_",
            'FBXSDKVersion': [
                {'value': 'FBX | FBX202000', "default": True},
                {'value': 'FBX | FBX201900'},
                {'value': 'FBX | FBX201800'},
                {'value': 'FBX | FBX201600'},
                {'value': 'FBX | FBX201400'},
                {'value': 'FBX | FBX201300'},
                {'value': 'FBX | FBX201200'},
                {'value': 'FBX | FBX201100'},
                {'value': 'FBX 6.0 | FBX201000'},
                {'value': 'FBX 6.0 | FBX200900'},
                {'value': 'FBX 6.0 | FBX200611'},
            ],
            'FBXVertexCacheFormat': [
                {'label': 'Maya Compatible (MC)', 'value': 'mayaformat'},
                {'label': '3DS Max Compatible (PC2)', 'value': 'maxformat'},
            ],
            'FBXExportInvisibleObjects': [
                {'label': 'As hidden null nodes', 'value': 'nullnodes'},
                {'label': 'As hidden full nodes', 'value': 'fullnodes'},
                {'label': 'As visible full nodes', 'value': 'visiblenodes'},
                {'label': 'Dont export', 'value': 'nonodes'},
            ],
            'FBXAxisSystem': [
                {'label': 'Y Up (Right-handed)', 'value': 'yupright'},
                {'label': 'Y Up (Left-handed)', 'value': 'yupleft'},
                {'label': 'Z Up (Right-handed)', 'value': 'zupright'},
                {'label': 'Current (Y up Right-handed)', 'value': 'currentup'},
            ],
            'FBXConversionLevelOfDetail': "1.0",
            'FBXDetectConstantPointCountDynamicObjects': False,
            'FBXConvertNURBSAndBeizerSurfaceToPolygons': False,
            'FBXConserveMemoryAtTheExpenseOfExportTime': False,
            'FBXForceBlendShapeExport': False,
            'FBXForceSkinDeformExport': False,
            'FBXExportEndEffectors': True,
        }

    def get_options_group_name(self):
        '''Override'''
        return 'FBX exporter options'

    def build(self):
        '''build function , mostly used to create the widgets.'''

        self.update(self.define_options())

        super(HoudiniFbxPublisherExporterOptionsWidget, self).build()

    def on_fetch_callback(self, result):
        '''This function is called by the _set_internal_run_result function of
        the BaseOptionsWidget'''
        # self._get_widget('FBXFrameRangeStart').setText(
        #    str(result['frameStart'])
        # )
        # self._get_widget('FBXFrameRangeEnd').setText(str(result['frameEnd']))


class HoudiniFbxPublisherExporterOptionsPluginWidget(
    plugin.HoudiniPublisherExporterPluginWidget
):
    plugin_name = 'houdini_fbx_publisher_exporter'
    widget = HoudiniFbxPublisherExporterOptionsWidget


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = HoudiniFbxPublisherExporterOptionsPluginWidget(api_object)
    plugin.register()
