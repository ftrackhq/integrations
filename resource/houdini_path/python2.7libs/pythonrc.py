# :coding: utf-8
# :copyright: Copyright (c) 2014-2021 ftrack

import os
import tempfile
import logging

import hou, hdefereval

from ftrack_connect_pipeline_qt import event
from ftrack_connect_pipeline import constants
from ftrack_connect_pipeline_houdini import host as houdini_host

import ftrack_api

from ftrack_connect_pipeline.configure_logging import configure_logging

configure_logging(
    'ftrack_connect_pipeline_houdini',
    extra_modules=['ftrack_connect_pipeline', 'ftrack_connect_pipeline_qt'],
    propagate=False
)

logger = logging.getLogger('ftrack_connect_pipeline_houdini')

event_manager = None

def init():
    global event_manager

    session = ftrack_api.Session(auto_connect_event_hub=False)

    event_manager = event.QEventManager(
        session=session, mode=constants.LOCAL_EVENT_MODE
    )

    houdini_host.HoudiniHost(event_manager)

    def setFrameRangeData():

        start_frame = float(os.getenv('FS', 1001))
        end_frame = float(os.getenv('FE', 1101))
        shot_id = os.getenv('FTRACK_SHOTID')
        fps = 24.0
        handles = 0.0

        try:
            shot = session.query('Shot where id={}'.format(shot_id)).one()
            if 'fps' in shot['custom_attributes'].keys():
                fps = float(shot['custom_attributes']['fps'])
            if 'handles' in shot['custom_attributes']:
                handles = float(shot['custom_attributes']['handles'])
        except Exception as error:
            logger.error(error)

        logger.info('setting timeline to {} {} '.format(start_frame, end_frame))

        # add handles to start and end frame
        hsf = (start_frame - 1) - handles
        hef = end_frame + handles

        hou.setFps(fps)
        hou.setFrame(start_frame)

        try:
            if start_frame != end_frame:
                hou.hscript('tset {0} {1}'.format(hsf / fps, hef / fps))
                hou.playbar.setPlaybackRange(start_frame, end_frame)
        except IndexError:
            pass

    try:
        setFrameRangeData()
    except Exception as error:
        # Continue execution if this fails
        logger.error(error)


def writePypanel(panel_id):
    ''' Write temporary xml file for pypanel '''
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<pythonPanelDocument>
  <interface name="{0}" label="{0}" icon="MISC_python" help_url="">
    <script><![CDATA[

import __main__

def createInterface():

    info_view = __main__.showPipelineDialog('{0}')

    return info_view]]></script>
    <help><![CDATA[]]></help>
  </interface>
</pythonPanelDocument>"""

    xml = xml.format(panel_id)

    path = os.path.join(tempfile.gettempdir(), 'ftrack', 'connect',
                        '{}.pypanel'.format(panel_id))
    if os.path.exists(path):
        pass
    else:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        f = open(path, 'w')
        f.write(xml)
        f.close()
    return path


def FtrackPipelineDialogs(panel_id):
    ''' Generate Dialog and create pypanel instance '''

    pan_path = writePypanel(panel_id)
    hou.pypanel.installFile(pan_path)

    ftrack_id = 'Ftrack_ID'
    panel_interface = None

    try:
        for interface, value in hou.pypanel.interfaces().items():
            if interface == panel_id:
                panel_interface = value
                break
    except hou.OperationFailed as e:
        logger.error('Something Wrong with Python Panel: {}'.format(e))

    main_tab = hou.ui.curDesktop().findPaneTab(ftrack_id)

    if main_tab:
        panel = main_tab.pane().createTab(hou.paneTabType.PythonPanel)
        panel.showToolbar(False)
        panel.setActiveInterface(panel_interface)
    else:
        if panel_interface:
            hou.hscript('pane -S -m pythonpanel -o -n {}'.format(ftrack_id))
            panel = hou.ui.curDesktop().findPaneTab(ftrack_id)
            panel.showToolbar(False)
            panel.setActiveInterface(panel_interface)


def showPipelineDialog(name):
    ''' Show Dialog '''

    from ftrack_connect_pipeline_houdini.client import load
    from ftrack_connect_pipeline_houdini.client import publish
    from ftrack_connect_pipeline_houdini.client import asset_manager
    from ftrack_connect_pipeline_houdini.client import log_viewer

    if 'Loader' in name:
        dialog = load.HoudiniLoaderClient(event_manager)
    elif 'Manager' in name:
        dialog = asset_manager.HoudiniAssetManagerClient(event_manager)
    elif 'LogViewer' in name:
        dialog = log_viewer.HoudiniLogViewerClient(event_manager)
    else:
        dialog = publish.HoudiniPublisherClient(event_manager)

    return dialog


hdefereval.executeDeferred(init)