# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import logging

import nuke

logger = logging.getLogger(__name__)


def init_nuke(context_id=None, session=None):
    '''
    Initialise timeline in Nuke based on shot/asset build settings.

    :param session:
    :param from_context: If True, the timeline data should be fetched from current context instead of environment variables.
    :return:
    '''
    fstart = fend = fps = None
    if context_id:
        context = session.query(
            'Context where id={}'.format(context_id)
        ).first()
        if context is None:
            logger.error(
                'Cannot initialize Nuke timeline - no such context: {}'.format(
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
                'Cannot initialize Nuke timeline - no shot related to context: {}'.format(
                    context_id
                )
            )
            return
        elif (
            not 'fstart' in shot['custom_attributes']
            or not 'fend' in shot['custom_attributes']
        ):
            logger.warning(
                'Cannot initialize Nuke timeline - no fstart or fend shot custom attributes available'.format()
            )
            return
        if 'fstart' in shot['custom_attributes']:
            fstart = int(shot['custom_attributes']['fstart'])
        if 'fend' in shot['custom_attributes']:
            fend = int(shot['custom_attributes']['fend'])
        if 'fps' in shot['custom_attributes']:
            fps = float(shot['custom_attributes']['fps'])
    else:
        # Set default values from environments.
        if 'FS' in os.environ and len(os.environ['FS'] or '') > 0:
            fstart = os.environ.get('FS', 0)
        if 'FE' in os.environ and len(os.environ['FE'] or '') > 0:
            fend = os.environ.get('FE', 100)
        if 'FPS' in os.environ:
            fps = float(os.environ['FPS'])

    if fstart is not None and fend is not None:
        nuke.root().knob("lock_range").setValue(False)
        logger.info('Setting start frame : {}'.format(fstart))
        nuke.knob('root.first_frame', str(fstart))
        logger.info('Setting end frame : {}'.format(fend))
        nuke.knob('root.last_frame', str(fend))
        nuke.root().knob("lock_range").setValue(True)
    if fps is not None:
        logger.info('Setting FPS : {}'.format(fps))
        nuke.root().knob("fps").setValue(fps)
