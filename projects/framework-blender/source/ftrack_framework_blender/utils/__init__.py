# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from functools import wraps
from typing import Callable

import bpy


def delegate_to_main_thread_without_result(f: Callable) -> None:
    """Make sure a function runs in the Blender main thread."""

    @wraps(f)
    def decorated(*args, **kwargs):
        deferred_f_with_args = lambda: f(*args, **kwargs)
        bpy.app.timers.register(deferred_f_with_args)

        # while bpy.app.timers.is_registered(deferred_f_with_args):
        #     print("Function playblast/ops still registered/running")
        #     time.sleep(0.5)

    return decorated


def blender_operator(f: Callable) -> None:
    """Turn the function into a temporary blender operator"""

    @wraps(f)
    def decorated(*args, **kwargs):
        class TemporaryOperator(bpy.types.Operator):
            bl_idname = "ftrack.temp_operator"
            bl_label = "Ftrack Temporary Operator"
            bl_undo_group = "Ftrack Temporary Operator"

            def execute(self, context):
                try:
                    bpy.ops.ed.undo_push(message="Temp Undo Group")
                    f(*args, **kwargs)
                except Exception as error:
                    raise error
                finally:
                    bpy.ops.ed.undo()
                return {'FINISHED'}

        try:
            bpy.utils.register_class(TemporaryOperator)
            context_override = None
            for screen in bpy.data.screens:
                for area in screen.areas:
                    if area.type == "VIEW_3D":
                        context_override = {"area": area, "screen": screen}

            assert context_override, "Context could not be set correctly"

            with bpy.context.temp_override(**context_override):
                bpy.ops.ftrack.temp_operator()

        except Exception as error:
            raise error
        finally:
            bpy.utils.unregister_class(TemporaryOperator)

    return decorated


# class BlenderPluginExecutionError(PluginExecutionError):
#     def __init__(self, message: str, error_type: str, operator) -> None:
#         super(PluginExecutionError).__init__(message)

# def get_context(_type):
#     for screen in bpy.data.screens:
#         for area in screen.areas:
#             if area.type == _type:
#                 context_override = {"area": area, "screen": screen}
#                 return context_override
#
#
# override = get_context("VIEW_3D")
#
# with bpy.context.temp_override(**override):
#     bpy.ops.ed.undo_push(message="ftrack: Export Thumbnail")
