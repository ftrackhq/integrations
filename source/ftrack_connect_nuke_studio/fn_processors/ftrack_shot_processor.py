# Copyright (c) 2011 The Foundry Visionmongers Ltd.  All Rights Reserved.
import tempfile
import os
from .ftrack_base import FtrackBase
from hiero.exporters.FnShotProcessor import ShotProcessor, ShotProcessorPreset

 

class FtrackShotProcessor(ShotProcessor, FtrackBase):

    def __init__(self, preset, submission, synchronous=False):
        ShotProcessor.__init__(self, preset, submission, synchronous=synchronous)
        FtrackBase.__init__(self)

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
        result = self.session.query('ProjectSchema where name is "Film Pipeline"').first()
        # self.logger.info('Project schema: %s' % result['name'])
        return result

    @property
    def task_type(self):
        result =  self.schema.get_types('Task')[0]
        # self.logger.info('task_type: %s' % result['name'])
        return result

    @property
    def task_status(self):
        result =  self.schema.get_statuses('Task', self.task_type['id'])[0]
        # self.logger.info('task_status: %s' % result['name'])
        return result

    @property
    def shot_status(self):
        result =  self.schema.get_statuses('Shot')[0]
        # self.logger.info('shot_status: %s' % result['name'])
        return result

    @property
    def asset_type(self):
        return self.session.query('AssetType where short is "geo"').first()
    
    @property
    def asset_version_status(self):
        result =  self.schema.get_statuses('AssetVersion')[0]
        return 

    def _create_project_fragment(self, name, parent):
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

    def _create_sequence_fragment(self, name, parent):
        sequence = self.session.query(
            'Sequence where name is "{}" and parent.id is "{}"'.format(name, parent['id'])
        ).first()
        if not sequence:
            sequence = self.session.create('Sequence', {
                'name': name,
                'parent': parent
            })          
        return sequence

    def _create_shot_fragment(self, name, parent):
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

    def _create_asset_fragment(self, name, parent):
        asset = self.session.query(
            'Asset where name is "{}" and parent.id is "{}"'.format(name, parent['parent']['id'])
        ).first()
        if not asset:
            asset = self.session.create('Asset', {
                'name': name,
                'parent': parent['parent'],
                'type': self.asset_type
            })
        
        comment = 'Published with : {}.{}.{}'.format(*self.hiero_version_touple)

        version = self.session.create('AssetVersion', {
            'asset': asset,
            'status': self.asset_version_status,
            'comment': comment,
            'task': parent
        })

        return version

    def _create_task_fragment(self, name, parent):
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

    def _create_component_fragment(self, name, parent):
        component = parent.create_component('/', {
            'name': name
        }, location=None)

        return component


    def _skip_fragment(self, name, parent):
        self.logger.warning('Skpping : {}'.format(name))
        
    def create_project_structure(self, task):
        for (export_path, preset) in self._exportTemplate.flatten():
            preset_name = preset.name()
            path = task.resolvePath(export_path)
            parent = None

            for template, token in zip(export_path.split(os.path.sep), path.split(os.path.sep)):
                self.logger.info('%s , %s ' % (template, token))

                fragment_fn = self.fn_mapping.get(template, self._skip_fragment)
                self.logger.info('creating : {} as {}'.format(template, token))
                parent = fragment_fn(token, parent)

            self.session.commit()

    def processTaskPreQueue(self):
        super(FtrackShotProcessor, self).processTaskPreQueue()
        for taskGroup in self._submission.children():
            for task in taskGroup.children():
                self.logger.info('Processing Task pre queue: %s' % task)
                self.create_project_structure(task)

        self.session.commit()

    # def startProcessing(self, exportItems, preview=False):
    #     if not preview:
    #         self.logger.info('!!!!!!!!!! Processing: %s, is preview %s' % (exportItems, preview))
    #     # if not preview:.....
    #     # for item in exportItems:
    #     #     self.create_project_structure(item)

    #     result = super(FtrackShotProcessor, self).startProcessing(exportItems, preview=preview)
    #     if not preview:
    #         self.logger.info('!!!!!!!!!! Processing: DONE')

    #     return result

class FtrackShotProcessorPreset(ShotProcessorPreset, FtrackBase):

    def __init__(self, name, properties):
        super(FtrackShotProcessorPreset, self).__init__(
            name, properties
        )
        FtrackBase.__init__(self)
        self._parentType = FtrackShotProcessor
        self.set_export_root()
        self.set_ftrack_properties()

    def set_ftrack_properties(self):
        self.properties()['ftrackProperties'] = {}
        ftrack_properties = self.properties()['ftrackProperties']
        # here we can add any custom property to check later.

    def set_export_root(self):
        accessor_prefix = self.ftrack_location.accessor.prefix
        self.properties()["exportRoot"] = accessor_prefix

    def resolve_ftrack_project(self, task):
        return task.projectName()

    def resolve_ftrack_sequence(self, task):
        trackItem = task._item
        return trackItem.name().split('_')[0]

    def resolve_ftrack_shot(self, task):
        trackItem = task._item
        return trackItem.name().split('_')[1]        
    
    def resolve_ftrack_task(self, task):
        # TODO: here we should really parse the task tags and use the ftrack task tag to define ?
        # let's stick to something basic for now
        return 'Compositing'

    def resolve_ftrack_asset(self, task):
        # for now simply return the component
        return self.resolve_ftrack_component(task)

    def resolve_ftrack_component(self, task):
        # TODO: Check whether there's a better way to get this out !
        preset_name =  vars(task)['_preset'].name()
        return preset_name

    def resolve_ftrack_version(self, task):
        return "0" # here we can check if there's any tag with an id to check against, if not we can return 0 as first version        

    def addUserResolveEntries(self, resolver):
        
        resolver.addResolver(
            "{ftrack_project}",
            "Ftrack project path.",
            lambda keyword, task: self.resolve_ftrack_project(task)
        )

        resolver.addResolver(
            "{ftrack_sequence}",
            "Ftrack sequence path.",
            lambda keyword, task: self.resolve_ftrack_sequence(task)
        )

        resolver.addResolver(
            "{ftrack_shot}",
            "Ftrack shot path.",
            lambda keyword, task: self.resolve_ftrack_shot(task)
        )

        resolver.addResolver(
            "{ftrack_task}",
            "Ftrack task path.",
            lambda keyword, task: self.resolve_ftrack_task(task)
        )

        resolver.addResolver(
            "{ftrack_asset}",
            "Ftrack asset path.",
            lambda keyword, task: self.resolve_ftrack_asset(task)
        )

        resolver.addResolver(
            "{ftrack_version}",
            "Ftrack version.",
            lambda keyword, task: self.resolve_ftrack_version(task)
        )

        resolver.addResolver(
            "{ftrack_component}",
            "Ftrack component path.",
            lambda keyword, task: self.resolve_ftrack_component(task)
        )
