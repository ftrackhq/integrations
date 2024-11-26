# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import bpy

from ftrack_utils.paths import get_temp_path

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import (
    PluginExecutionError,
    PluginValidationError,
)


class BlenderObjectModeValidatorPlugin(BasePlugin):
    name = "blender_object_mode_validator"

    def set_mesh_objects_to_object_mode(
        self, store, mesh_objects_in_edit_mode
    ):
        """
        Set all mesh objects that are currently in edit mode to object mode.
        """

        active_object = bpy.context.view_layer.objects.active
        try:
            for obj in mesh_objects_in_edit_mode:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode="OBJECT")
        except Exception as error:
            raise PluginExecutionError(message=error)
        finally:
            bpy.context.view_layer.objects.active = active_object

    def run(self, store):
        """
        Checks if any mesh objects are currently in edit mode.
        We can only export a selection if all mesh objects are in object mode.
        """

        mesh_objects_in_edit_mode = [
            obj
            for obj in bpy.context.scene.objects
            if obj.type == "MESH" and obj.mode == "EDIT"
        ]

        if mesh_objects_in_edit_mode:
            self.logger.warning(
                f'Some objects are still in EDIT mode. {[_.name for _ in mesh_objects_in_edit_mode]}'
            )
            raise PluginValidationError(
                message=f"Some objects are still in EDIT mode. Can't export scene.",
                on_fix_callback=lambda _: self.set_mesh_objects_to_object_mode(
                    store, mesh_objects_in_edit_mode
                ),
            )

        self.logger.debug("All mesh objects are properly set to object mode.")
