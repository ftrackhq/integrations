# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
#
import logging

import flame

from ftrack_framework_flame import get_ftrack_menu

logger = logging.getLogger('ftrack_framework_flame.init')


# https://help.autodesk.com/view/FLAME/2022/ENU/?guid=Flame_API_Python_Hooks_Reference_html

def get_timeline_custom_ui_actions():
    #  Adds custom actions to the contextual menu available in the Timeline.
    show_on = (flame.PySegment)
    return get_ftrack_menu(show_on)
