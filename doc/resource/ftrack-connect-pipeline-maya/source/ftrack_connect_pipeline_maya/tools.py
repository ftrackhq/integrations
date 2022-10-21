# :coding: utf-8
# :copyright: Copyright (c) 2022 ftrack

import os
import shutil

import ftrack_api

import maya.cmds as cmds

from ftrack_connect_pipeline.utils import (
    get_save_path,
)


def scene_open(session, logger):
    '''Load latest scene, or generate new from template.'''
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
        path_snapshot_load = path_snapshot_open

    if path_snapshot_load:
        # Load the scene
        logger.info('Loading scene: {}'.format(path_snapshot_load))
        cmds.file(path_snapshot_load, open=True, force=True)
