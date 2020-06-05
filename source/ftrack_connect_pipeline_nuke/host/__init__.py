# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import logging
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_nuke import constants as nuke_constants
from ftrack_connect_pipeline.host import Host

import nuke

logger = logging.getLogger(
    __name__
)


def get_ftrack_menu(menu_name = 'ftrack_pipeline'):
    '''Get the current ftrack menu, create it if does not exists.'''

    nuke_menu = nuke.menu("Nuke")
    ftrack_menu = nuke_menu.findItem('ftrack_pipeline')
    if not ftrack_menu:
        ftrack_menu = nuke_menu.addMenu(menu_name)

    return ftrack_menu


class NukeHost(Host):
    host = [qt_constants.HOST, nuke_constants.HOST]