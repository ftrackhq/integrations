# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import os

import maya.cmds as cmds

logger = logging.getLogger(__name__)


def init_maya(context_id=None, session=None):
    '''
    Initialise timeline in Maya based on shot/asset build settings.

    :param session:
    :param context_id: If provided, the timeline data should be fetched this context instead of environment variables.
    :param session: The session required to query from *context_id*.
    :return:
    '''
    fstart = fend = fps = None
    if context_id:
        assert session is not None, 'Session not provided'
        context = session.query(
            'Context where id={}'.format(context_id)
        ).first()
        if context is None:
            logger.error(
                'Cannot initialize Maya timeline - no such context: {}'.format(
                    context_id
                )
            )
            return
        shot = None
        if context.entity_type == 'Shot':
            shot = context
        elif context.entity_type == 'Task':
            parent = context['parent']
            if parent.entity_type == 'Shot':
                shot = parent
        if not shot:
            logger.warning(
                'Cannot initialize Maya timeline - no shot related to context: {}'.format(
                    context_id
                )
            )
            return
        elif (
            not 'fstart' in shot['custom_attributes']
            or not 'fend' in shot['custom_attributes']
        ):
            logger.warning(
                'Cannot initialize Maya timeline - no fstart or fend shot custom attributes available'.format()
            )
            return
        if 'fstart' in shot['custom_attributes']:
            fstart = float(shot['custom_attributes']['fstart'])
        if 'fend' in shot['custom_attributes']:
            fend = float(shot['custom_attributes']['fend'])
        if 'fps' in shot['custom_attributes']:
            fps = float(shot['custom_attributes']['fps'])
    else:
        # Set default values from environments.
        if 'FS' in os.environ and len(os.environ['FS'] or '') > 0:
            fstart = float(os.environ.get('FS', 0))
        if 'FE' in os.environ and len(os.environ['FE'] or '') > 0:
            fend = float(os.environ.get('FE', 100))
        if 'FPS' in os.environ and len(os.environ['FPS'] or '') > 0:
            fps = float(os.environ['FPS'])

    if fstart is not None and fend is not None:
        logger.info('Setting start frame : {}'.format(fstart))
        cmds.setAttr('defaultRenderGlobals.startFrame', fstart)

        logger.info('Setting end frame : {}'.format(fend))
        cmds.setAttr('defaultRenderGlobals.endFrame', fend)

        cmds.playbackOptions(min=fstart, max=fend)

    if fps is not None:
        fps_unit = "film"
        if fps == 15:
            fps_unit = "game"
        elif fps == 25:
            fps_unit = "pal"
        elif fps == 30:
            fps_unit = "ntsc"
        elif fps == 48:
            fps_unit = "show"
        elif fps == 50:
            fps_unit = "palf"
        elif fps == 60:
            fps_unit = "ntscf"
        logger.info('Setting FPS : {}, unit: {}'.format(fps, fps_unit))
        cmds.currentUnit(time=fps_unit)
