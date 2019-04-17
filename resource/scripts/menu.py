# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import logging
import re
from ftrack_connect_pipeline_nuke import usage, host as nuke_host
from ftrack_connect_pipeline import event, host
from ftrack_connect_pipeline.session import get_shared_session
from ftrack_connect_pipeline_nuke import constants


logger = logging.getLogger('ftrack_connect_pipeline_nuke.scripts.userSetup')

created_dialogs = dict()


def open_dialog(dialog_class, hostid):
    '''Open *dialog_class* and create if not already existing.'''
    dialog_name = dialog_class

    if dialog_name not in created_dialogs:
        ftrack_dialog = dialog_class
        created_dialogs[dialog_name] = ftrack_dialog(
            hostid
        )

    created_dialogs[dialog_name].show()


def initialise():
    # TODO : later we need to bring back here all the nuke initialiations from ftrack-connect-nuke
    # such as frame start / end etc....
    session = get_shared_session()
    hostid = host.initialise(session, constants.HOST, constants.UI)
    menu = nuke_host.get_ftrack_menu()
    print hostid, menu






initialise()
