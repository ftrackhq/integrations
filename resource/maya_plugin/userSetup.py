# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


import logging
import threading

from ftrack_connect_pipeline import host

import ftrack_connect_pipeline_maya #  import to configure logging

import maya.cmds as mc

logger = logging.getLogger('userSetup')


def register_hub_host():
    t = threading.Thread(target=host.start_host_listener)
    t.daemon = True
    t.start()
    logger.info('thread started!')


mc.evalDeferred("register_hub_host()")
