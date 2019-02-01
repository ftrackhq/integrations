# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack


import logging
import threading
import re
from ftrack_connect_pipeline import host
from ftrack_connect_pipeline import usage
import ftrack_connect_pipeline_maya #  import to configure logging

import maya.cmds as mc

logger = logging.getLogger('userSetup')


def load_and_int():
    # TODO : later we need to bring back here all the maya initialiations from ftrack-connect-maya
    # such as frame start / end etc....

    usage.send_event(
        'USED-FTRACK-CONNECT-PIPELINE-MAYA'
    )

    if mc.about(win=True):
        match = re.match(
            '([0-9]{4}).*', mc.about(version=True)
        )

        if int(match.groups()[0]) >= 2018:
            import QtExt

            # Disable web widgets.
            QtExt.is_webwidget_supported = lambda: False

            logger.debug(
                'Disabling webwidgets due to maya 2018 '
                'QtWebEngineWidgets incompatibility.'
            )




def register_hub_host():
    t = threading.Thread(target=host.start_host_listener)
    t.daemon = True
    t.start()
    logger.info('thread started!')


mc.evalDeferred("register_hub_host()")
mc.evalDeferred("load_and_init()")
