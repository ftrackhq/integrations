# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import os
import shutil

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


def scene_open(session, logger):
    '''Load latest scene, or generate new from template.'''
    from ftrack_framework_maya.utils import get_save_path

    context_id = os.getenv('FTRACK_CONTEXTID')
    task = session.query('Task where id={}'.format(context_id)).one()
    path_snapshot_open = path_snapshot_load = None
    path_snapshot, message = get_save_path(
        context_id, session, extension='.mb', temp=True
    )
    location = session.pick_location()
    for version in session.query(
        'AssetVersion where '
        'task.id={} order by date descending'.format(
            task['id'],
        )
    ).all():
        # Find a snapshot
        component = session.query(
            'Component where '
            'name="snapshot" and version.id={}'.format(version['id'])
        ).first()
        if component:
            try:
                path_snapshot_open = location.get_filesystem_path(component)
            except ftrack_api.exception.ComponentNotInLocationError as e:
                cmds.confirmDialog(message=str(e))

    if path_snapshot_open is None:
        # Copy Maya template scene
        path_template = os.path.join(
            location.accessor.prefix,
            task['project']['name'],
            '_TEMPLATES',
            'maya',
            '{}_template.mb'.format(task['type']['name'].lower()),
        )
        if os.path.exists(path_template):
            logger.info(
                'Copying Maya template {} to {}'.format(
                    path_template, path_snapshot
                )
            )
            shutil.copy(path_template, path_snapshot)
            path_snapshot_load = path_snapshot
        else:
            logger.warning(
                'Maya template not found @ {}!'.format(path_template)
            )
    else:
        # Make a copy in temp
        logger.info(
            'Copying most recent snapshot {} to {}'.format(
                path_snapshot_open, path_snapshot
            )
        )
        shutil.copy(path_snapshot_open, path_snapshot)
        path_snapshot_load = path_snapshot

    if path_snapshot_load:
        # Load the scene
        logger.info('Loading scene: {}'.format(path_snapshot_load))
        cmds.file(path_snapshot_load, open=True, force=True)


def set_task_status(status_name, session, logger, unused_arg=None):
    '''Change the status of the launched task to *status*'''
    task = session.query(
        'Task where id={}'.format(os.environ['FTRACK_CONTEXTID'])
    ).one()
    status = session.query('Status where name="{}"'.format(status_name)).one()
    logger.info(
        'Changing status of task {} to {}'.format(task['name'], status_name)
    )
    task['status'] = status
    session.commit()
