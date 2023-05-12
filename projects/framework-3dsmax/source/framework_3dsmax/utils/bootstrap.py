# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os
import logging

from pymxs import runtime as rt

logger = logging.getLogger(__name__)


def init_max(context_id=None, session=None):
    '''
    Initialise timeline in Max based on shot/asset build settings.

    :param context_id: If provided, the timeline data should be fetched this context instead of environment variables.
    :param session: The session required to query from *context_id*.
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
        logger.info('Setting animation range : {}-{}'.format(fstart, fend))
        rt.animationRange = rt.interval(fstart, fend)

    # TODO: Set FPS through Python API
