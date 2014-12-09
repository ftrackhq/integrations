import tempfile
from ftrack_connect_nuke_studio.processor import BasePlugin


class PublishPlugin(BasePlugin):
    def __init__(self):
        name = 'processor.publish'
        super(PublishPlugin, self).__init__(name=name)

        self.defaults = {
            "OUT":{
                'file_type': 'dpx',
                'afterRender': 'from ftrack_connect_nuke_studio.nuke_publish_cb import createComponent;createComponent()'
            }
         }

        self.script = '${FTRACK_PROCESSOR_PLUGIN_PATH}/publish.nk'

    def manage_options(self, data):
        ''' for informational purpose only here we show the manage_input function
        '''
        data = super(PublishPlugin, self).manage_options(data)
        # define the output file sequence
        format = '.####.%s' % data['OUT']['file_type']
        name = self.name.replace('.', '_')
        tmp = tempfile.NamedTemporaryFile(suffix=format, delete=False, prefix=name)
        data['OUT']['file'] = tmp.name
        return data


class ProxyPlugin(BasePlugin):
    def __init__(self):
        name = 'processor.proxy'
        super(ProxyPlugin, self).__init__(name=name)

        image_scale = 0.5

        self.defaults = {
            "OUT":{
                'file_type': 'png',
                'afterRender': 'from ftrack_connect_nuke_studio.nuke_publish_cb import createComponent;createComponent()'
            },
            'REFORMAT':{
                'type': "to box",
                'scale': image_scale
            }
         }

        self.script = '${FTRACK_PROCESSOR_PLUGIN_PATH}/publish.nk'

    def manage_options(self, data):
        ''' for informational purpose only here we show the manage_input function
        '''
        data = super(ProxyPlugin, self).manage_options(data)
        # define the output file sequence
        format = '.####.%s' % data['OUT']['file_type']
        name = self.name.replace('.', '_')
        tmp = tempfile.NamedTemporaryFile(suffix=format, delete=False, prefix=name)
        data['OUT']['file'] = tmp.name
        return data


class ReviewPlugin(BasePlugin):
    def __init__(self):
        name = 'processor.review'
        super(ReviewPlugin, self).__init__(name=name)
        self.format = '.mov'

        self.defaults = {
            'OUT':{
                'file_type': 'mov',
                'mov64_codec': 'jpeg',
                'afterRender': 'from ftrack_connect_nuke_studio.nuke_publish_cb import createReview;createReview()'
            }
        }

        self.script = '${FTRACK_PROCESSOR_PLUGIN_PATH}/review.nk'

    def manage_options(self, data):
        data = super(ReviewPlugin, self).manage_options(data)
        # define the output file
        name = self.name.replace('.', '_')
        tmp = tempfile.NamedTemporaryFile(suffix=self.format, delete=False, prefix=name)
        data['OUT']['file'] = tmp.name
        return data



class ThumbnailPlugin(BasePlugin):
    def __init__(self):
        name = 'processor.thumbnail'
        super(ThumbnailPlugin, self).__init__(name=name)

        self.chosen_frame = 1001

        self.defaults = {
            'OUT':{
                'file_type': 'jpeg',
                'first': self.chosen_frame,
                'last': self.chosen_frame,
                'afterRender': 'from ftrack_connect_nuke_studio.nuke_publish_cb import createThumbnail;createThumbnail()'
            }
        }

        self.script = '${FTRACK_PROCESSOR_PLUGIN_PATH}/thumbnail.nk'

    def manage_options(self, data):

        data = super(ThumbnailPlugin, self).manage_options(data)
        # define the output file sequence
        format = '.%s.%s' % (self.chosen_frame, data['OUT']['file_type'])
        name = self.name.replace('.', '_')
        tmp = tempfile.NamedTemporaryFile(suffix=format, delete=False, prefix=name)
        data['OUT']['file'] = tmp.name
        return data



def register(registry):
    # create and register plugin instances
    plugin_publish = PublishPlugin()
    registry.add(plugin_publish)

    plugin_review = ReviewPlugin()
    registry.add(plugin_review)

    plugin_thumbnail = ThumbnailPlugin()
    registry.add(plugin_thumbnail)

    plugin_proxy = ProxyPlugin()
    registry.add(plugin_proxy)