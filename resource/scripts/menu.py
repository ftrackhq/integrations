# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import logging

from ftrack_connect_pipeline_nuke import usage, host as nuke_host
from ftrack_connect_pipeline import event, host, utils
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline_nuke import constants
from ftrack_connect_pipeline_nuke.menu import build_menu_widgets
import ftrack_connect_pipeline_nuke

import sys
import traceback

logger = logging.getLogger('ftrack_connect_pipeline_nuke.scripts.userSetup')


def initialise():
    # TODO : later we need to bring back here all the nuke initialiations from ftrack-connect-nuke
    # such as frame start / end etc....
    session = get_shared_session()
    hostid = host.initialise(session, constants.HOST, constants.UI)

    usage.send_event(
        'USED-FTRACK-CONNECT-PIPELINE-NUKE'
    )

    # Enable loader and publisher only if is set to run local (default)
    remote_set = utils.remote_event_mode()
    ftrack_menu = nuke_host.get_ftrack_menu()

    if not remote_set:
        try:
            build_menu_widgets(ftrack_menu, hostid)
        except:
            traceback.print_exc(file=sys.stdout)

    else:
        nuke_host.notify_connected_client(session, hostid)





initialise()
