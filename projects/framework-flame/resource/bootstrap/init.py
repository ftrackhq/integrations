# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
#
import flame

import logging
import functools
from ftrack_framework_flame import bootstrap_integration

from ftrack_utils.extensions.environment import (
    get_extensions_path_from_environment,
)

logger = logging.getLogger('ftrack_framework_flame.init')


def on_run_tool_callback(
    client_instance, tool_name, dialog_name=None, options=dict, maya_args=None
):
    client_instance.run_tool(
        tool_name,
        dialog_name,
        options,
    )


# https://help.autodesk.com/view/FLAME/2022/ENU/?guid=Flame_API_Python_Hooks_Reference_html

def get_mediahub_files_custom_ui_actions():
    # Adds custom actions in the MediaHub's Files browser. The path of the selection object can be obtained using .path .
    return get_main_menu_custom_ui_actions()

def get_mediahub_projects_custom_ui_actions():
    #  Adds custom actions in the MediaHub's Projects browser. The path of the selection object can be obtained using .uid
    return get_main_menu_custom_ui_actions()

def get_mediahub_archives_custom_ui_actions():
    # Adds custom actions in the MediaHub's Archives browser. There is no selection returned for an archive,
    # so the hook can only be used to trigger an operation from the Archive panel. It cannot affect its content.
    return get_main_menu_custom_ui_actions()

def get_batch_custom_ui_actions():
    # Adds custom actions to the contextual menu available in Batch.
    return get_main_menu_custom_ui_actions()

def get_timeline_custom_ui_actions():
    #  Adds custom actions to the contextual menu available in the Timeline.
    return get_main_menu_custom_ui_actions()

def get_action_custom_ui_actions():
    #  Adds custom actions to the contextual menu available in the Batch Action node.
    return get_main_menu_custom_ui_actions()


def get_main_menu_custom_ui_actions():
    client_instance, registry_instance = bootstrap_integration(get_extensions_path_from_environment())

    dcc_config = registry_instance.get_one(
        name='framework-flame', extension_type='dcc_config'
    )['extension']

    logger.debug(f'Read DCC config: {dcc_config}')

    # Create ftrack menu
    actions = []
    # Register tools into ftrack menu
    for tool in dcc_config['tools']:
        run_on = tool.get("run_on")
        on_menu = tool.get("menu", True)
        if on_menu:
            new_action = {
                'name': tool['label'],
                'execute': functools.partial(
                        on_run_tool_callback,
                        client_instance,
                        tool.get('name'),
                        tool.get('dialog_name'),
                        tool['options'],
                ),
                'minimumVersion': '2023'
            }
            actions.append(new_action)

        if run_on:
            if run_on == "startup":
                # Execute startup tool-configs
                on_run_tool_callback(
                    client_instance,
                    tool.get('name'),
                    tool.get('dialog_name'),
                    tool['options'],
                )
            else:
                logger.error(
                    f"Unsupported run_on value: {run_on} tool section of the "
                    f"tool {tool.get('name')} on the tool config file: "
                    f"{dcc_config['name']}. \n Currently supported values:"
                    f" [startup]"
                )

    return [
        {
            "name": "ftrack",
            "actions": actions
        }
    ]