import os
import hiero
import logging
import ftrack_api

class FtrackBase(object):
    '''
    wrap ftrack functionalities and methods
    '''
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )
        self.logger.setLevel(logging.DEBUG)
        self.session = ftrack_api.Session()

    @property
    def hiero_version_touple(self):
        return (
            hiero.core.env['VersionMajor'],
            hiero.core.env['VersionMinor'],
            hiero.core.env['VersionRelease'].split('v')[-1]
        )

    @property
    def ftrack_location(self):
        result = self.session.pick_location()    
        self.logger.info('location: %s' % result)
        return result

    @property
    def ftrack_origin_location(self):
        return self.session.query(
            'Location where name is "ftrack.origin"'
        ).one()

    @property
    def ftrack_server_location(self):
        return self.session.query(
            'Location where name is "ftrack.server"'
        ).one()


class FtrackBaseProcessorPreset(FtrackBase):
    def __init__(self, *args, **kwargs):
        super(FtrackBaseProcessor, self).__init__(*args, **kwargs)
        self._parentType = FtrackShotProcessor
        self.set_export_root()
        self.set_ftrack_properties(properties)

    def set_ftrack_properties(self, properties):
        self.properties()['ftrack'] = {}
        ftrack_properties = self.properties()['ftrack']

        # add placeholders for default ftrack defaults
        ftrack_properties['project_schema'] = 'Film Pipeline'
        ftrack_properties['task_type'] = 'Compositing'
        ftrack_properties['task_status'] = 'Not Started'
        ftrack_properties['shot_status'] = 'In progress'
        ftrack_properties['asset_version_status'] = 'WIP'

        # override properties from processor setup
        if 'ftrack' in properties:
            self.properties()['ftrack'].update(properties['ftrack'])
        else:
            self.logger.info('no ftrack settings found in {0}'.format(properties))

    def set_export_root(self):
        self.properties()["exportRoot"] = self.ftrack_location.accessor.prefix

    def resolve_ftrack_project(self, task):
        return task.projectName()

    def resolve_ftrack_sequence(self, task):
        trackItem = task._item
        return trackItem.name().split('_')[0]

    def resolve_ftrack_shot(self, task):
        trackItem = task._item
        return trackItem.name().split('_')[1]        
    
    def resolve_ftrack_task(self, task):
        return self.properties()['ftrack']['task_type']

    def resolve_ftrack_asset(self, task):
        return task._preset.name()

    def resolve_ftrack_component(self, task):
        return 'main' # these component will go all under main

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


class FtrackBaseProcessor(FtrackBase):
    def __init__(self, *args, **kwargs):
        super(FtrackBaseProcessor, self).__init__(*args, **kwargs)
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
        ).one()
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
        
    def create_project_structure(self, task, trackItem):
        file_name = task._preset.properties()['ftrack']['component_pattern']

        preset_name = task._preset.name()
        resolved_file_name = task.resolvePath(file_name)
        path = task.resolvePath(task._shotPath)
        export_path = task._shotPath
        parent = None # after the loop this will be containing the component object

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

        return parent