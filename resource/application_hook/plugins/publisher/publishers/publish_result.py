# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import os
from ftrack_connect_pipeline import plugin


class FtrackPublishPlugin(plugin.PublisherPlugin):
    plugin_name = 'result'

    def run(self, context=None, data=None, options=None):

        asset_name = context['asset_name']
        asset_type = context['asset_type']
        context_object = self.session.get('Context', context['context_id'])
        asset_type_object = self.session.query('AssetType where short is "{}"'.format(asset_type)).first()
        asset_parent_object = context_object['parent']

        location = self.session.pick_location()

        asset_object = self.session.query(
            'Asset where name is "{}" and type.short is "{}" and parent.id is "{}"'.format(
                asset_name, asset_type, asset_parent_object['id'])
        ).first()

        if not asset_object:
            asset_object = self.session.create('Asset', {
                'name': asset_name,
                'type': asset_type_object,
                'parent': asset_parent_object
            })

        asset_version = self.session.create('AssetVersion', {
            'asset': asset_object,
            'task': context_object,
        })

        self.session.commit()

        for component_name, component_path in data.items():
            asset_version.create_component(
                component_path[1],
                data={'name': component_name},
                location=location
            )
        self.session.commit()

        self.logger.debug("publishing: {} to {} as {}".format(data, context, asset_object))
        return True


def register(api_object, **kw):
    plugin = FtrackPublishPlugin(api_object)
    plugin.register()
