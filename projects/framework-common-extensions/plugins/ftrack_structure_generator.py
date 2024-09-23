# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import os
import traceback

from ftrack_framework_core.plugin import BasePlugin
from ftrack_framework_core.exceptions.plugin import PluginExecutionError


class FtrackStructureGeneratorPlugin(BasePlugin):
    name = 'ftrack_structure_generator'

    def run(self, store):
        '''
        This method expects to receive a dictionary in the given *data* with all
        the previous steps plugin results. Will look for all the components
        exporter plugins in the given *data* and will publish the result to its
        component name in ftrack.
        '''

        # Get components to publish
        collected_objects = store.get('collected_objects')
        if not collected_objects:
            raise PluginExecutionError(
                'No collected_objects found to publish. '
                'Please check your previous steps plugins.'
            )

        # We could use the context widget to determine the project where this
        # objects will be published but for the prototype to keep the simplicity
        # I will use the project key of the collected objects.

        # for each object on coollected_object, we will generate all the structure in ftrack based on the following keys: sequence_name, shot_name, task_name, component_name, if any of the entities doesn't exits we will create it, and if it exists we will publish the object into it.
        for obj in collected_objects:
            project_name = obj.get('project_name')
            sequence_name = obj.get('sequence_name')
            shot_name = obj.get('shot_name')
            task_name = obj.get('task_name')
            asset_name = obj.get('asset_name')
            version_number = obj.get('version')
            object_path = obj.get('obj_path')

            if not all(
                [
                    project_name,
                    sequence_name,
                    shot_name,
                    task_name,
                    asset_name,
                    version_number,
                ]
            ):
                raise PluginExecutionError(
                    'Missing required keys in collected object: '
                    'project_name, sequence_name, shot_name, task_name, asset_name, version_number'
                )

            project_entity = self.session.query(
                f'select id from Project where name is "{project_name}"'
            ).first()
            if not project_entity:
                raise PluginExecutionError(
                    f'Project not found: {project_name}'
                )

            project_id = project_entity['id']

            # Check or create sequence
            sequence_entity = self.session.query(
                f'select id from Sequence where name is "{sequence_name}" and project.id is "{project_id}"'
            ).first()
            if not sequence_entity:
                sequence_entity = self.session.create(
                    'Sequence',
                    {'name': sequence_name, 'parent': project_entity},
                )
            self.session.commit()

            # Check or create shot
            shot_entity = self.session.query(
                f'Shot where name is "{shot_name}" and parent.id is "{sequence_entity["id"]}"'
            ).first()
            if not shot_entity:
                shot_entity = self.session.create(
                    'Shot', {'name': shot_name, 'parent': sequence_entity}
                )
            self.session.commit()

            # Check or create task
            task_entity = self.session.query(
                f'select id from Task where name is "{task_name}" and parent.id is "{shot_entity["id"]}"'
            ).first()
            if not task_entity:
                task_entity = self.session.create(
                    'Task', {'name': task_name, 'parent': shot_entity}
                )
            self.session.commit()

            # Check or create asset
            asset_type_name = 'script'
            asset_type_entity = self.session.query(
                'select name from AssetType where short is "{}"'.format(
                    asset_type_name
                )
            ).one()
            asset_entity = self.session.query(
                f'select id from Asset where name is "{asset_name}" and type.short is {asset_type_name} and parent.id is "{shot_entity["id"]}"'
            ).first()
            if not asset_entity:
                asset_entity = self.session.create(
                    'Asset',
                    {
                        'name': asset_name,
                        'type': asset_type_entity,
                        'parent': shot_entity,
                    },
                )
            self.session.commit()

            # Check or create asset version
            # TODO: take into account that we should update the verision on the filenames to not get desync
            status = self.session.query(
                'Status where name is "In Progress"'
            ).first()
            asset_version_entity = self.session.create(
                'AssetVersion',
                {
                    'asset': asset_entity,
                    'task': task_entity,
                    'comment': 'This is a test',
                    'status': status,
                },
            )
            self.session.commit()

            # Extract the extension from the object_path
            component_name = os.path.splitext(object_path)[1][1:]

            location = self.session.pick_location()

            asset_version_entity.create_component(
                object_path, data={'name': component_name}, location=location
            )

            self.session.commit()
