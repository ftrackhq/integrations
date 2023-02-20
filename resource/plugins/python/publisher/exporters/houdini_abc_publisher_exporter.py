# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import tempfile

import hou

from ftrack_connect_pipeline_houdini import plugin
import ftrack_api


class HoudiniAbcPublisherExporterPlugin(plugin.HoudiniPublisherExporterPlugin):

    plugin_name = 'houdini_abc_publisher_exporter'

    def fetch(self, context_data=None, data=None, options=None):
        '''Fetch start and end frames from the scene'''
        r = hou.playbar.frameRange()
        frame_info = {'frameStart': r[0], 'frameEnd': r[1]}
        return frame_info

    def extract_options(self, options):
        r = hou.playbar.frameRange()
        return {
            'ABCAnimation': bool(options.get('ABCAnimation', True)),
            'ABCFrameRangeStart': float(
                options.get('ABCFrameRangeStart', r[0])
            ),
            'ABCFrameRangeEnd': float(options.get('ABCFrameRangeEnd', r[1])),
            'ABCFrameRangeBy': float(options.get('ABCFrameRangeBy', '1.0')),
        }

    def bake_camera_animation(self, node, frameRange):
        '''Bake camera to World Space'''
        if 'cam' in node.type().name():
            bake_node = hou.node('/obj').createNode(
                'cam', '%s_bake' % node.name()
            )

            for x in ['resx', 'resy']:
                bake_node.parm(x).set(node.parm(x).eval())

        for frame in range(int(frameRange[0]), (int(frameRange[1]) + 1)):
            time = (frame - 1) / hou.fps()
            matrix = node.worldTransformAtTime(time).explode()

            for parm in matrix:
                if 'shear' not in parm:
                    for x, p in enumerate(bake_node.parmTuple(parm[0])):
                        p.setKeyframe(hou.Keyframe(matrix[parm][x], time))

        return bake_node

    def run(self, context_data=None, data=None, options=None):
        '''Export collected object paths provided with *data* to a Alembic files'''
        new_file_path = tempfile.NamedTemporaryFile(
            delete=False, suffix='.abc'
        ).name

        options = self.extract_options(options)

        houdini_root_object = hou.node('/obj')

        collected_objects = []
        for collector in data:
            collected_objects.extend(collector['result'])
        if context_data['asset_type_name'] == 'cam':
            obj_path = collected_objects[0]
            bcam = self.bake_camera_animation(
                hou.node(obj_path),
                [options['ABCFrameRangeStart'], options['ABCFrameRangeEnd']],
            )
            objects = [bcam]
            object_paths = bcam.path()
        else:
            objects = [hou.node(obj_path) for obj_path in collected_objects]
            object_paths = ' '.join(collected_objects)

        # Create Rop Net
        rop_net = None
        try:
            rop_net = houdini_root_object.createNode('ropnet')
            abc_ropnet = rop_net.createNode('alembic')

            if options.get('ABCAnimation'):
                # Check Alembic for animation option
                abc_ropnet.parm('trange').set(1)
                for i, x in enumerate(
                    [
                        'ABCFrameRangeStart',
                        'ABCFrameRangeEnd',
                        'ABCFrameRangeBy',
                    ]
                ):
                    abc_ropnet.parm('f%d' % (i + 1)).deleteAllKeyframes()
                    abc_ropnet.parm('f%d' % (i + 1)).set(options[x])
            else:
                abc_ropnet.parm('trange').set(0)

            abc_ropnet.parm('filename').set(new_file_path)

            root_object = objects[0]
            abc_ropnet.parm('root').set(root_object.parent().path())
            abc_ropnet.parm('objects').set(object_paths)
            if options.get('ABCFormat') == 'HDF5':
                abc_ropnet.parm('format').set('hdf5')
            elif options.get('ABCFormat') == 'Ogawa':
                abc_ropnet.parm('format').set('ogawa')

            self.logger.debug(
                'Running Alembic export of "{}" to: {}'.format(
                    object_paths, new_file_path
                )
            )

            abc_ropnet.render()
        finally:
            if rop_net:
                rop_net.destroy()

        return [new_file_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    ma_plugin = HoudiniAbcPublisherExporterPlugin(api_object)
    ma_plugin.register()
