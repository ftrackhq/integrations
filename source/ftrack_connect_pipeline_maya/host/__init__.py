

import functools
import logging
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_maya import constants as maya_constants
from ftrack_connect_pipeline.host import Host

import maya.cmds as mc
import maya.mel as mm

logger = logging.getLogger(
    __name__
)


def get_ftrack_menu(menu_name = 'ftrack_pipeline'):
    '''Get the current ftrack menu, create it if does not exists.'''
    gMainWindow = mm.eval('$temp1=$gMainWindow')

    if mc.menu(
            menu_name,
            exists=True,
            parent=gMainWindow,
            label=menu_name
    ):
        menu = menu_name

    else:
        menu = mc.menu(
            menu_name,
            parent=gMainWindow,
            tearOff=False,
            label=menu_name
        )

    return menu


class MayaHost(Host):
    host = [qt_constants.HOST, maya_constants.HOST]