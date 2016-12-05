import pyblish.api


class CollectMayaCamera(pyblish.api.ContextPlugin):
    '''Collect maya cameras from scene.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add maya camera instances.'''
        instance = context.create_instance(
            'camera1', families=['ftrack', 'camera']
        )
        instance.data['publish'] = True
        instance.data['options'] = {
            'bake_camera': True,
            'start_frame_camera': 1001,
            'end_frame_camera': 1316
        }
        instance.data['ftrack_components'] = []

        instance2 = context.create_instance(
            'camera2', families=['ftrack', 'camera']
        )
        instance2.data['ftrack_components'] = []


class ExtractMayaBinaryCamera(pyblish.api.InstancePlugin):
    '''Extract maya cameras from scene.'''

    label = 'Maya binary'

    order = pyblish.api.ExtractorOrder

    families = ['camera']

    def process(self, instance):
        '''Process *instance* and extract maya camera.'''
        if instance.data.get('publish'):
            print (
                'Extracting maya binary camera using options:',
                instance.data.get('options')
            )
            instance.data['ftrack_components'].append(
                {
                    'name': instance.name,
                    'path': '/foo/bar/path/to/mayabinary/' + instance.name,
                }
            )


class ExtractMayaAlembicCamera(pyblish.api.InstancePlugin):
    '''Extract maya cameras from scene.'''

    label = 'Publish Alembic'

    order = pyblish.api.ExtractorOrder

    families = ['camera']

    optional = True

    def process(self, instance):
        '''Process *instance* and extract maya camera.'''
        if instance.data.get('publish'):
            print (
                'Extracting alembic camera using options:',
                instance.data.get('options')
            )
            instance.data['ftrack_components'].append(
                {
                    'name': instance.name,
                    'path': '/foo/bar/path/to/alembic/' + instance.name,
                }
            )

pyblish.api.register_plugin(CollectMayaCamera)
pyblish.api.register_plugin(ExtractMayaBinaryCamera)
pyblish.api.register_plugin(ExtractMayaAlembicCamera)
