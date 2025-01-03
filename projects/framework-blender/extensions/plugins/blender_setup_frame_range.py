# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import bpy
from bpy.app.handlers import persistent

from functools import partial
from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class BlenderSetupFrameRangeStartupPlugin(BasePlugin):
    name = 'blender_setup_frame_range'

    def run(self, store):
        '''
        Set the blender frame range and frame rate from the ftrack custom attributes
        '''

        task = self.session.get('Context', self.context_id)
        self.logger.debug(f'calling bpy.app.handlers.load_post.append with {task}')
        st_frame = int(task['parent']['custom_attributes'].get(
            'fstart', 1
        ))
        end_frame = int(task['parent']['custom_attributes'].get(
            'fend', 100
        ))
        fps = int(task['parent']['custom_attributes'].get(
            'fps', 24
        ))

        @persistent
        def load_handler(*args, **kwargs):
            # args[0] is the scene, which will be an empty string in case of
            # the startup scene    print(args, args[0]=="")
            if args[0] == '':
                self.logger.debug(f'calling load_handler to set timeline with {st_frame}, {end_frame}, {fps}')
                bpy.context.scene.frame_end = end_frame
                bpy.context.scene.frame_start = st_frame
                bpy.context.scene.render.fps = fps

        self.logger.debug(f'registering load_handler to set timeline with {st_frame}, {end_frame}, {fps}')
        bpy.app.handlers.load_post.append(load_handler)