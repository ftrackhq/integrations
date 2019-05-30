import functools
import logging

import MaxPlus

from ftrack_connect_pipeline import constants

logger = logging.getLogger(__name__)


def get_ftrack_menu(menu_name='ftrack_pipeline'):
    '''Get the current ftrack menu, create it if does not exists.'''
    if not MaxPlus.MenuManager.MenuExists(menu_name):
        MaxPlus.MenuBuilder(menu_name).Create(MaxPlus.MenuManager.GetMainMenu())

    return MaxPlus.MenuBuilder(menu_name)


def mark_menu(hostid, event):
    '''mark menu as connected or disconnnected.'''
    # TODO(spettrborg) Find out how to rename menus in Max
    client_hostid = event['data']['pipeline']['hostid']
    menu_builder = get_ftrack_menu()
    if client_hostid == hostid:
        logger.info('client connected')
        # mc.menu(menu, e=True, l='ftrack_pipeline (connected)')
        # TODO: Mark somehow the menu to be connected
    else:
        logger.info('client disconnected')
        # mc.menu(menu, e=True, l='ftrack_pipeline')
        # TODO: remove marked menu


def notify_connected_client(session, hostid):
    '''event handler to notify connected clients.'''
    event_handler = functools.partial(mark_menu, hostid)

    session.event_hub.subscribe(
        'topic={}'.format(constants.PIPELINE_CONNECT_CLIENT), event_handler
    )
