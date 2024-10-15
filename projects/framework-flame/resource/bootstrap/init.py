# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
#
import flame

import logging
from ftrack_framework_flame import bootstrap_integration, on_run_tool_callback, get_ftrack_menu

from ftrack_utils.extensions.environment import (
    get_extensions_path_from_environment,
)

logger = logging.getLogger('ftrack_framework_flame.init')


# https://help.autodesk.com/view/FLAME/2022/ENU/?guid=Flame_API_Python_Hooks_Reference_html


def get_timeline_custom_ui_actions():
    #  Adds custom actions to the contextual menu available in the Timeline.
    show_on = (flame.PySegment)
    return get_ftrack_menu(show_on)


# DISABLED

# def get_mediahub_files_custom_ui_actions():
#     # Adds custom actions in the MediaHub's Files browser. The path of the selection object can be obtained using .path .
#     return get_ftrack_menu()

#
# def get_media_panel_custom_ui_actions():
#     return get_ftrack_menu()
#
# def get_main_menu_custom_ui_actions():
#     return get_ftrack_menu()

# def get_action_custom_ui_actions():
#     #  Adds custom actions to the contextual menu available in the Batch Action node.
#     return get_ftrack_menu()

# def get_mediahub_projects_custom_ui_actions():
#     #  Adds custom actions in the MediaHub's Projects browser. The path of the selection object can be obtained using .uid
#     return get_ftrack_menu()
#
# def get_mediahub_archives_custom_ui_actions():
#     # Adds custom actions in the MediaHub's Archives browser. There is no selection returned for an archive,
#     # so the hook can only be used to trigger an operation from the Archive panel. It cannot affect its content.
#     return get_ftrack_menu()
#
# def get_batch_custom_ui_actions():
#     # Adds custom actions to the contextual menu available in Batch.
#     return get_ftrack_menu()

