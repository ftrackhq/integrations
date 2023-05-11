# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import tempfile

import hou

from ftrack_connect_pipeline_houdini import plugin
import ftrack_api


class HoudiniFbxPublisherExporterPlugin(plugin.HoudiniPublisherExporterPlugin):
    plugin_name = 'houdini_fbx_publisher_exporter'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch start and end frames from the scene'''
        r = hou.playbar.frameRange()
        frame_info = {'frameStart': r[0], 'frameEnd': r[1]}
        return frame_info

    def extract_options(self, options):
        r = hou.playbar.frameRange()
        return {
            'FBXASCII': bool(options.get('FBXASCII', True)),
            'FBXValidFrameRange': float(options.get('FBXCValidFrameRange', 0)),
            'FBXFrameRangeStart': float(
                options.get('FBXFrameRangeStart', r[0])
            ),
            'FBXFrameRangeEnd': float(options.get('FBXFrameRangeEnd', r[1])),
            'FBXFrameRangeBy': float(options.get('FBXFrameRangeBy', '1.0')),
            'FBXTake': str(options.get('FBXTake', '_current_')),
            'FBXSDKVersion': str(
                options.get('FBXExportScaleFactor', 'FBX | FBX202000')
            ),
            'FBXVertexCacheFormat': str(
                options.get('FBXVertexCacheFormat', 'mayaformat')
            ),
            'FBXExportInvisibleObjects': str(
                options.get('FBXExportInvisibleObjects', 'nullnodes')
            ),
            'FBXAxisSystem': str(options.get('FBXAxisSystem', 'yupright')),
            'FBXConversionLevelOfDetail': float(
                options.get('FBXConversionLevelOfDetail', '1.0')
            ),
            'FBXDetectConstantPointCountDynamicObjects': bool(
                options.get('FBXDetectConstantPointCountDynamicObjects', False)
            ),
            'FBXConvertNURBSAndBeizerSurfaceToPolygons': bool(
                options.get('FBXConvertNURBSAndBeizerSurfaceToPolygons', False)
            ),
            'FBXConserveMemoryAtTheExpenseOfExportTime': bool(
                options.get('FBXConserveMemoryAtTheExpenseOfExportTime', False)
            ),
            'FBXForceBlendShapeExport': bool(
                options.get('FBXForceBlendShapeExport', False)
            ),
            'FBXForceSkinDeformExport': bool(
                options.get('FBXForceSkinDeformExport', False)
            ),
            'FBXExportEndEffectors': bool(
                options.get('FBXExportEndEffectors', True)
            ),
        }

    def run(self, context_data=None, data=None, options=None):
        '''Export collected object paths provided with *data* to a FBX files'''

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.fbx'
        ).name

        options = self.extract_options(options)

        self.logger.debug(
            'Calling exporters options: data {}. options {}'.format(
                data, options
            )
        )

        root_obj = hou.node('/obj')

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        object_paths = ' '.join(collected_objects)
        objects = [hou.node(obj_path) for obj_path in collected_objects]
        ropNet = None
        try:
            # Create Rop Net
            ropNet = root_obj.createNode('ropnet')
            fbxRopnet = ropNet.createNode('filmboxfbx')

            fbxRopnet.parm('trange').set(options['FBXValidFrameRange'])
            fbxRopnet.parm('f1').set(options['FBXFrameRangeStart'])
            fbxRopnet.parm('f2').set(options['FBXFrameRangeEnd'])
            fbxRopnet.parm('f3').set(options['FBXFrameRangeBy'])
            fbxRopnet.parm('take').set(options['FBXTake'])
            fbxRopnet.parm('trange').set(options['FBXValidFrameRange'])
            fbxRopnet.parm('sopoutput').set(new_file_path)
            fbxRopnet.parm('startnode').set(objects[0].parent().path())
            fbxRopnet.parm('exportkind').set(options['FBXASCII'])
            fbxRopnet.parm('sdkversion').set(options['FBXSDKVersion'])
            fbxRopnet.parm('vcformat').set(options['FBXVertexCacheFormat'])
            fbxRopnet.parm('invisobj').set(
                options['FBXExportInvisibleObjects']
            )
            fbxRopnet.parm('polylod').set(
                options['FBXConversionLevelOfDetail']
            )
            fbxRopnet.parm('detectconstpointobjs').set(
                options['FBXDetectConstantPointCountDynamicObjects']
            )
            fbxRopnet.parm('convertsurfaces').set(
                options['FBXConvertNURBSAndBeizerSurfaceToPolygons']
            )
            fbxRopnet.parm('conservemem').set(
                options['FBXConserveMemoryAtTheExpenseOfExportTime']
            )
            fbxRopnet.parm('forceblendshape').set(
                options['FBXForceBlendShapeExport']
            )
            fbxRopnet.parm('forceskindeform').set(
                options['FBXForceSkinDeformExport']
            )
            fbxRopnet.parm('axissystem').set(options['FBXAxisSystem'])
            fbxRopnet.parm('exportendeffectors').set(
                options['FBXExportEndEffectors']
            )
            fbxRopnet.render()
        except Exception as e:
            self.logger.exception(e)
            return False, {'message': 'Failed to export Alembic: {}'.format(e)}
        finally:
            if ropNet:
                ropNet.destroy()

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    ma_plugin = HoudiniFbxPublisherExporterPlugin(api_object)
    ma_plugin.register()
