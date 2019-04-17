import functools
import logging

import nuke

from ftrack_connect_pipeline import constants

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


def mark_menu(hostid, event):
    '''mark menu as connected or disconnnected.'''
    client_hostid = event['data']['pipeline']['hostid']
    menu = get_ftrack_menu()
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
        'topic={}'.format(
            constants.PIPELINE_CONNECT_CLIENT
        ),
        event_handler
    )



