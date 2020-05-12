# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import functools
import logging

from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_3dsmax import constants as max_constants
from ftrack_connect_pipeline.host import Host

import MaxPlus

logger = logging.getLogger(__name__)

def get_ftrack_menu(menu_name='ftrack_pipeline'):
    '''Get the current ftrack menu'''
    ftrack_menu = MaxPlus.MenuManager.FindMenu(menu_name)

    return ftrack_menu


class MaxHost(Host):
    host = [qt_constants.HOST, max_constants.HOST]
