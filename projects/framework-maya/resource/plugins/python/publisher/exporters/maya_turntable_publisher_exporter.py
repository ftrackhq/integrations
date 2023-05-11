# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack

import tempfile
import glob
import platform
import sys

import ftrack_api

from ftrack_connect_pipeline_maya import plugin

import maya.cmds as cmds


class MayaTurntablePublisherExporterPlugin(plugin.MayaPublisherExporterPlugin):
    '''Maya turntable reviewable publisher plugin'''

    plugin_name = 'maya_turntable_publisher_exporter'

    def run(self, context_data=None, data=None, options=None):
        '''Render a turntable out of the camera and selected objects provided in *data*'''
        camera_name = data[0]['result'][0]
        collected_objects = data[1]['result']

        self.logger.debug(f'turntable - camera {camera_name}')
        self.logger.debug(f'turntable - collected_objects {collected_objects}')
        self.logger.debug(f'turntable - objects {collected_objects}')

        res_w = int(cmds.getAttr('defaultResolution.width'))
        res_h = int(cmds.getAttr('defaultResolution.height'))

        sframe = cmds.playbackOptions(q=True, min=True)
        eframe = cmds.playbackOptions(q=True, max=True)

        # Ensure 50 frames are always set as minimum.
        if eframe - sframe < 50:
            eframe = sframe + 50

        undo = False
        try:
            cmds.undoInfo(openChunk=True)
            self.setup_turntable(collected_objects, sframe, eframe)
            undo = True
            result = self.run_reviewable(
                camera_name, sframe, eframe, res_w, res_h
            )
        finally:
            cmds.undoInfo(closeChunk=True)
            if undo:
                cmds.undo()
        return result

    def setup_turntable(self, collected_objects, sframe, eframe):
        '''Prepare the Maya scene to create a turntable of the *collected_objects*
        centered, considering the bounding boxes and the configured up axis.'''
        # Find bounding box for all objects
        bb_collected_objects = [
            sys.maxsize,
            sys.maxsize,
            sys.maxsize,
            -sys.maxsize,
            -sys.maxsize,
            -sys.maxsize,
        ]
        for object in collected_objects:
            selected_object = object
            if 'transform' != cmds.nodeType(selected_object):
                parent = cmds.listRelatives(selected_object, parent=True)
                selected_object = parent[0]

            bb_vertices = cmds.exactWorldBoundingBox(selected_object)
            # Return :value
            # float[]
            # xmin, ymin, zmin, xmax, ymax, zmax

            for idx in range(0, 3):
                if bb_vertices[idx] < bb_collected_objects[idx]:
                    bb_collected_objects[idx] = bb_vertices[idx]
            for idx in range(3, 6):
                if bb_vertices[idx] > bb_collected_objects[idx]:
                    bb_collected_objects[idx] = bb_vertices[idx]

        x_loc = (bb_collected_objects[0] + bb_collected_objects[3]) / 2
        y_loc = bb_collected_objects[1]
        z_loc = (bb_collected_objects[2] + bb_collected_objects[5]) / 2
        object_locator = cmds.spaceLocator(
            absolute=True,
            position=[x_loc, y_loc, z_loc],
            name="object_locator",
        )

        cmds.setAttr(object_locator[0] + ".visibility", False)

        up_axis = cmds.upAxis(q=True, axis=True)
        rotate_attribute = 'rotate{}'.format(up_axis.upper())

        cmds.xform(object_locator, centerPivots=True)
        cmds.setKeyframe(
            object_locator, attribute=rotate_attribute, value=0, time=sframe
        )
        cmds.setKeyframe(
            object_locator,
            attribute=rotate_attribute,
            value=360,
            time=int(eframe) + 1,
        )
        cmds.keyTangent(
            object_locator,
            attribute=rotate_attribute,
            index=(0, 1),
            inTangentType="linear",
            outTangentType="linear",
        )
        group = cmds.group(empty=True)
        cmds.setAttr(group + ".translateX", x_loc)
        cmds.setAttr(group + ".translateY", y_loc)
        cmds.setAttr(group + ".translateZ", z_loc)
        cmds.xform(group, centerPivots=True)
        for object in collected_objects:
            selected_object = object
            if 'transform' != cmds.nodeType(selected_object):
                parent = cmds.listRelatives(selected_object, parent=True)
                selected_object = parent[0]
            cmds.parent(selected_object, group)
        cmds.orientConstraint(object_locator, group)

    def run_reviewable(self, camera_name, sframe, eframe, res_w, res_h):
        '''Run a playblast through camera identified by *camera_name*, starting at frame
        *sframe* and ending at *efram* at resolution *res_w* x *res_h*'''
        current_panel = cmds.getPanel(wf=True)
        panel_type = cmds.getPanel(to=current_panel)  # scriptedPanel
        if panel_type != 'modelPanel':
            visible_panels = cmds.getPanel(vis=True)
            for _panel in visible_panels:
                if cmds.getPanel(to=_panel) == 'modelPanel':
                    current_panel = _panel
                    break
                else:
                    current_panel = None

        previous_camera = 'persp'
        if current_panel:
            previous_camera = cmds.modelPanel(
                current_panel, q=True, camera=True
            )

        cmds.lookThru(camera_name)

        cmds.select(cl=True)

        filename = tempfile.NamedTemporaryFile().name

        playblast_data = dict(
            format='movie',
            sequenceTime=0,
            clearCache=1,
            viewer=0,
            offScreen=True,
            showOrnaments=0,
            frame=range(int(sframe), int(eframe + 1)),
            filename=filename,
            fp=4,
            percent=100,
            quality=70,
            w=res_w,
            h=res_h,
        )

        if 'linux' in platform.platform().lower():
            playblast_data['format'] = 'qt'
            playblast_data['compression'] = 'raw'

        cmds.playblast(**playblast_data)

        cmds.lookThru(previous_camera)

        temp_files = glob.glob(filename + '.*')
        # TODO:
        # find a better way to find the extension of the playblast file.
        full_path = temp_files[0]

        return [full_path]


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = MayaTurntablePublisherExporterPlugin(api_object)
    plugin.register()
