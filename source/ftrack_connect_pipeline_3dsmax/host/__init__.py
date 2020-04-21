# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import functools
import logging

from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_qt import constants as qt_constants
from ftrack_connect_pipeline_3dsmax import constants as max_constants
from ftrack_connect_pipeline.host import Host

import MaxPlus

logger = logging.getLogger(__name__)

def get_ftrack_menu(menu_name='ftrack_pipeline'):
    '''Get the current ftrack menu, create it if does not exists.'''
    ftrack_menu = MaxPlus.MenuManager.FindMenu('ftrack_pipeline')
    if not MaxPlus.MenuManager.MenuExists(menu_name):
        ftrack_menu = MaxPlus.MenuBuilder(menu_name).Create(
            MaxPlus.MenuManager.GetMainMenu()
        )

    return ftrack_menu

def mark_menu(hostid, event):
    '''mark menu as connected or disconnnected.'''
    # TODO(spettrborg) Find out how to rename menus in Max
    client_hostid = event['data']['pipeline']['hostid']
    if client_hostid == hostid:
        logger.info('client connected')
        # TODO: Mark somehow the menu to be connected
    else:
        logger.info('client disconnected')
        # TODO: remove marked menu


def notify_connected_client(session, hostid):
    '''event handler to notify connected clients.'''
    event_handler = functools.partial(mark_menu, hostid)

    session.event_hub.subscribe(
        'topic={}'.format(constants.PIPELINE_CONNECT_CLIENT), event_handler
    )


class MaxHost(Host):
    host = [qt_constants.HOST, max_constants.HOST]
