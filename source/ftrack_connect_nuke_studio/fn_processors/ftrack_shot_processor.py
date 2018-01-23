# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import tempfile
import os
from .ftrack_base import FtrackBase
from hiero.exporters.FnShotProcessor import ShotProcessor
from hiero.core.FnProcessor import _expandTaskGroup
 

class FtrackShotProcessor(ShotProcessor, FtrackBase):

    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackBase.__init__(self)
        self.ftrack_properties = self._preset.properties()['ftrack']

        # note we do resolve {ftrack_version} as part of the {ftrack_asset} function
        self.fn_mapping = {
            '{ftrack_project}': self._create_project_fragment,
            '{ftrack_sequence}': self._create_sequence_fragment,
            '{ftrack_shot}': self._create_shot_fragment,
            '{ftrack_task}': self._create_task_fragment,
            '{ftrack_asset}': self._create_asset_fragment,
            '{ftrack_component}': self._create_component_fragment
        }

    @property
    def schema(self):
        project_schema_name = self.ftrack_properties['project_schema']
        project_schema = self.session.query(
            'ProjectSchema where name is "{0}"'.format(project_schema_name)
        ).first()
        self.logger.info('project_schema: %s' % project_schema)
        return project_schema

    @property
    def task_type(self):
        task_type_name = self.ftrack_properties['task_type']
        task_types =  self.schema.get_types('Task')
        task_type = [t for t in task_types if t['name'] == task_type_name][0]
        self.logger.info('task_type: %s' % task_type)
        return task_type

    @property
    def task_status(self):
        task_status_name = self.ftrack_properties['task_status']
        task_statuses =  self.schema.get_statuses('Task', self.task_type['id'])
        task_status = [t for t in task_statuses if t['name'] == task_status_name][0]
        self.logger.info('task_status: %s' % task_status)
        return task_status

    @property
    def shot_status(self):
        shot_status_name = self.ftrack_properties['shot_status']
        shot_statuses =  self.schema.get_statuses('Shot')
        shot_status = [t for t in shot_statuses if t['name'] == shot_status_name][0]
        self.logger.info('shot_status: %s' % shot_status)
        return shot_status

    @property
    def asset_version_status(self):
        asset_status_name = self.ftrack_properties['asset_version_status']
        asset_statuses =  self.schema.get_statuses('AssetVersion')
        asset_status = [t for t in asset_statuses if t['name'] == asset_status_name][0]
        self.logger.info('asset_version_status: %s' % asset_status)
        return asset_status

    def asset_type_per_task(self, task):
        asset_type = task._preset.properties()['ftrack']['asset_type_code']
        result = self.session.query(
            'AssetType where short is "{}"'.format(asset_type)
        ).one()

        return result
    

    def _create_project_fragment(self, name, parent, task):
        project = self.session.query(
            'Project where name is "{}"'.format(name)
        ).first()
        if not project:
            project = self.session.create('Project', {
                'name': name,
                'full_name': name + '_full',
                'project_schema': self.schema
            })
        return project

    def _create_sequence_fragment(self, name, parent, task):
        sequence = self.session.query(
            'Sequence where name is "{}" and parent.id is "{}"'.format(name, parent['id'])
        ).first()
        if not sequence:
            sequence = self.session.create('Sequence', {
                'name': name,
                'parent': parent
            })          
        return sequence

    def _create_shot_fragment(self, name, parent, task):
        shot = self.session.query(
            'Shot where name is "{}" and parent.id is "{}"'.format(name, parent['id'])
        ).first()
        if not shot:
            shot = self.session.create('Shot', {
                'name': name,
                'parent': parent,
                'status': self.shot_status
            })
        return shot

    def _create_asset_fragment(self, name, parent, task):
        asset = self.session.query(
            'Asset where name is "{}" and parent.id is "{}"'.format(name, parent['parent']['id'])
        ).first()
        if not asset:
            asset = self.session.create('Asset', {
                'name': name,
                'parent': parent['parent'],
                'type': self.asset_type_per_task(task)
            })
        
        comment = 'Published from Nuke Studio : {}.{}.{}'.format(*self.hiero_version_touple)

        version = self.session.create('AssetVersion', {
            'asset': asset,
            'status': self.asset_version_status,
            'comment': comment,
            'task': parent
        })

        return version

    def _create_task_fragment(self, name, parent, task):
        task = self.session.query(
            'Task where name is "{}" and parent.id is "{}"'.format(name, parent['id'])
        ).first()
        if not task:
            task = self.session.create('Task', {
                'name': name,
                'parent': parent,
                'status': self.task_status,
                'type': self.task_type
            })                    
        return task

    def _create_component_fragment(self, name, parent, task):
        asset_type = task._preset.properties()['ftrack']['asset_type_code']
        component = parent.create_component('/', {
            'name': name
        }, location=None)

        return component

    def _skip_fragment(self, name, parent):
        self.logger.warning('Skpping : {}'.format(name))
        
    def create_project_structure(self, task):
        file_name = task._preset.properties()['ftrack']['component_pattern']

        preset_name = task._preset.name()
        resolved_file_name = task.resolvePath(file_name)
        path = task.resolvePath(task._shotPath)
        export_path = task._shotPath
        parent = None

        for template, token in zip(export_path.split(os.path.sep), path.split(os.path.sep)):
            fragment_fn = self.fn_mapping.get(template, self._skip_fragment)
            parent = fragment_fn(token, parent, task)

        self.session.commit()

        # extract ftrack path from structure and accessors
        ftrack_shot_path = self.ftrack_location.structure.get_resource_identifier(parent)
        ftrack_path = os.path.join(self.ftrack_location.accessor.prefix, ftrack_shot_path, resolved_file_name)

        # assign result path back to the tasks, so it knows where to render stuff out.
        task._exportPath = ftrack_path
        task._exportRoot = self.ftrack_location.accessor.prefix
        task._export_template = os.path.join(task._shotPath, file_name)

    def processTaskPreQueue(self):
        super(FtrackShotProcessor, self).processTaskPreQueue()
        for task in _expandTaskGroup(self._submission):
            self.create_project_structure(task)

    def startProcessing(self, exportItems, preview=False):
        result = super(FtrackShotProcessor, self).startProcessing(exportItems, preview=preview)


        return result
