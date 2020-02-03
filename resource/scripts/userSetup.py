# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
import logging
import re
from ftrack_connect_pipeline_maya import usage, host as maya_host
from ftrack_connect_pipeline import event, host
from ftrack_connect_pipeline import constants

import maya.cmds as mc
import maya.mel as mm

import ftrack_api

logger = logging.getLogger('ftrack_connect_pipeline_maya.scripts.userSetup')

created_dialogs = dict()

_shared_event_manager = None


def get_shared_event_manager():
    '''Return shared ftrack_api session.'''
    global _shared_event_manager

    if not _shared_event_manager:
        session = ftrack_api.Session(auto_connect_event_hub=False)
        _shared_event_manager = event.EventManager(
            session=session, mode=constants.LOCAL_EVENT_MODE
        )
        logger.debug('creating new session {}'.format(_shared_event_manager))

    return _shared_event_manager

def ready_callback(event):
    task = event['host_connection'].session.query(
        'select name from Task where project.name is "pipelinetest"'
    ).first()
    schema = task['project']['project_schema']
    task_status = schema.get_statuses('Task')[0]
    publisher = event['definition']
    publisher['contexts']['plugins'][0]['options']['context_id'] = task['id']
    publisher['contexts']['plugins'][0]['options']['asset_name'] = 'PipelineAsset'
    publisher['contexts']['plugins'][0]['options']['asset_type'] = 'geo'
    publisher['contexts']['plugins'][0]['options']['comment'] = 'A new hope'
    publisher['contexts']['plugins'][0]['options']['status_id'] = task_status['id']
    publisher['components'][0]['stages'][0]['plugins'][0]['options'][
        'path'] = "/Users/lluisftrack/Desktop/file_to_publish.txt"
    return publisher


def _open_dialog(dialog_class):#, hostid):
    '''Open *dialog_class* and create if not already existing.'''
    dialog_name = dialog_class
    event_manager = get_shared_event_manager()

    if dialog_name not in created_dialogs:
        ftrack_dialog = dialog_class
        created_dialogs[dialog_name] = ftrack_dialog(
            event_manager
        )
    #created_dialogs[dialog_name].on_ready(ready_callback, time_out=30)
    created_dialogs[dialog_name].show()


def initialise():
    # TODO : later we need to bring back here all the maya initialiations
    #  from ftrack-connect-maya
    # such as frame start / end etc....

    logger.info('Setting up the menu')

    event_manager = get_shared_event_manager()
    host.Host(event_manager, host=['maya'])

    usage.send_event(
        'USED-FTRACK-CONNECT-PIPELINE-MAYA'
    )

    mc.loadPlugin('ftrackMayaPlugin.py', quiet=True)

    from ftrack_connect_pipeline_maya.client import load
    from ftrack_connect_pipeline_maya.client import publish

    # Enable loader and publisher only if is set to run local (default)
    dialogs = []

    dialogs.append(
        (load.MayaLoaderClient, 'Loader')
    )
    dialogs.append(
        (publish.MayaPublisherClient, 'Publisher')
    )

    ftrack_menu = maya_host.get_ftrack_menu()
    # Register and hook the dialog in ftrack menu
    for item in dialogs:
        if item == 'divider':
            mc.menuItem(divider=True)
            continue

        dialog_class, label = item

        mc.menuItem(
            parent=ftrack_menu,
            label=label,
            command=(
                lambda x, dialog_class=dialog_class: _open_dialog(dialog_class)#, hostid)
            )
        )




mc.evalDeferred("initialise()", lp=True)
