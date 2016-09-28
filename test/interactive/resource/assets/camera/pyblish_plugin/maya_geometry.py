import pyblish.api


class CollectMayaGeometry(pyblish.api.ContextPlugin):
    '''Collect maya geometry from scene.'''

    order = pyblish.api.CollectorOrder

    def process(self, context):
        '''Process *context* and add maya geometry instances.'''
        context.create_instance('geometry1', family='geometry')
        context.create_instance('geometry2', family='geometry')


pyblish.api.register_plugin(CollectMayaGeometry)
