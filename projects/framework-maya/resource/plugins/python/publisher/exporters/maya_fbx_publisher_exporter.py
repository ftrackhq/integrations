# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import tempfile

import maya.cmds as cmds
import maya.mel as mel

from ftrack_connect_pipeline_maya import plugin
import ftrack_api


class MayaFbxPublisherExporterPlugin(plugin.MayaPublisherExporterPlugin):
    '''Maya FBX exporter plugin'''

    plugin_name = 'maya_fbx_publisher_exporter'

    def extract_options(self, options):

        return {
            'FBXExportScaleFactor': int(
                options.get('FBXExportScaleFactor', 1)
            ),
            'FBXExportUpAxis': str(options.get('FBXExportUpAxis', 'y')),
            'FBXExportFileVersion': str(
                options.get('FBXExportFileVersion', 'FBX201600')
            ),
            'FBXExportSmoothMesh': bool(
                options.get('FBXExportSmoothMesh', False)
            ),
            'FBXExportInAscii': bool(options.get('FBXExportInAscii', False)),
            'FBXExportAnimationOnly': bool(
                options.get('FBXExportAnimationOnly', False)
            ),
            'FBXExportInstances': bool(
                options.get('FBXExportInstances', False)
            ),
            'FBXExportApplyConstantKeyReducer': bool(
                options.get('FBXExportApplyConstantKeyReducer', False)
            ),
            'FBXExportBakeComplexAnimation': bool(
                options.get('FBXExportBakeComplexAnimation', False)
            ),
            'FBXExportBakeResampleAnimation': bool(
                options.get('FBXExportBakeResampleAnimation', False)
            ),
            'FBXExportCameras': bool(options.get('FBXExportCameras', True)),
            'FBXExportLights': bool(options.get('FBXExportLights', True)),
            'FBXExportConstraints': bool(
                options.get('FBXExportConstraints', False)
            ),
            'FBXExportEmbeddedTextures': bool(
                options.get('FBXExportEmbeddedTextures', False)
            ),
            'FBXExportQuaternion': options.get(
                'FBXExportQuaternion', 'quaternion'
            ),
            'FBXExportShapes': bool(options.get('FBXExportShapes', True)),
            'FBXExportSkins': bool(options.get('FBXExportSkins', True)),
            'FBXExportSkeletonDefinitions': bool(
                options.get('FBXExportSkeletonDefinitions', True)
            ),
            'FBXExportInputConnections': bool(
                options.get('FBXExportInputConnections', False)
            ),
            'FBXExportUseSceneName': bool(
                options.get('FBXExportUseSceneName', True)
            ),
        }

    def run(self, context_data=None, data=None, options=None):
        '''Export Maya FBX geometry based on collected objects in *data* and *options* supplied'''

        # ensure to load the fbx plugin
        cmds.loadPlugin('fbxmaya.so', qt=1)

        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.fbx'
        ).name

        options = self.extract_options(options)

        self.logger.debug(
            'Calling exporters options: data {}. options {}'.format(
                data, options
            )
        )

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])

        # fbx basic options
        mel.eval('FBXResetExport')
        mel.eval('FBXExportConvertUnitString "cm"')
        mel.eval('FBXExportGenerateLog -v 0')

        # fbx user options
        scale = options.get('FBXExportScaleFactor')
        mel.eval('FBXExportScaleFactor {}'.format(scale))

        up_axis = options.get('FBXExportUpAxis')
        mel.eval('FBXExportUpAxis {}'.format(up_axis))

        version = options.get('FBXExportFileVersion')
        mel.eval('FBXExportFileVersion {}'.format(version))

        smooth_mesh = options.get('FBXExportSmoothMesh')
        mel.eval('FBXExportSmoothMesh -v {}'.format(int(smooth_mesh)))

        ascii_export = options.get('FBXExportInAscii')
        mel.eval('FBXExportInAscii -v {}'.format(int(ascii_export)))

        anim_only = options.get('FBXExportAnimationOnly')
        mel.eval('FBXExportAnimationOnly -v {}'.format(int(anim_only)))

        intances = options.get('FBXExportInstances')
        mel.eval('FBXExportInstances -v {}'.format(int(intances)))

        constraint_reducer = options.get('FBXExportApplyConstantKeyReducer')
        mel.eval(
            'FBXExportApplyConstantKeyReducer -v {}'.format(
                int(constraint_reducer)
            )
        )

        bake_complex_anim = options.get('FBXExportBakeComplexAnimation')
        mel.eval(
            'FBXExportBakeComplexAnimation -v {}'.format(
                int(bake_complex_anim)
            )
        )

        bake_resample_anim = options.get('FBXExportBakeResampleAnimation')
        mel.eval(
            'FBXExportBakeResampleAnimation -v {}'.format(
                int(bake_resample_anim)
            )
        )

        export_camera = options.get('FBXExportCameras')
        mel.eval('FBXExportCameras -v {}'.format(int(export_camera)))

        export_constraints = options.get('FBXExportConstraints')
        mel.eval('FBXExportConstraints -v {}'.format(int(export_constraints)))

        embedded_textures = options.get('FBXExportEmbeddedTextures')
        mel.eval(
            'FBXExportEmbeddedTextures -v {}'.format(int(embedded_textures))
        )

        export_lights = options.get('FBXExportLights')
        mel.eval('FBXExportLights -v {}'.format(int(export_lights)))

        # fbx export command
        mel.eval(
            'FBXExport -s -f "{}"'.format(new_file_path.replace("\\", "\\\\"))
        )

        cmds.select(collected_objects, r=True)
        selectednodes = cmds.ls(sl=True, long=True)
        if selectednodes:
            cmds.select(selectednodes)

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    ma_plugin = MayaFbxPublisherExporterPlugin(api_object)
    ma_plugin.register()
