# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from ftrack_framework_plugin import BasePlugin
import ftrack_constants.framework as constants


class ComponentPathCollectorPlugin(BasePlugin):
    name = 'component_path_collector'

    def ui_hook(self, payload):
        '''
        if payload['context_type'] is 'asset': return all Assets on the given
        payload['context_id'] with asset type payload['asset_type_name']

        if payload['context_type'] is 'asset_version': return all
        AssetVersion entities available on the given
        payload['asset_id'] on task payload['context_id']
        '''
        context_id = payload['context_id']

        if payload.get('context_type', 'asset') == 'asset':
            asset_type_entity = self.session.query(
                'select name from AssetType where short is "{}"'.format(
                    payload['asset_type_name']
                )
            ).one()

            # Determine if we have a task or not
            context = self.session.get('Context', context_id)
            # If it's a fake asset, context will be None so return empty list.
            if not context:
                return []
            if context.entity_type == 'Task':
                assets = self.session.query(
                    'select name, versions.task.id, type.id, id, latest_version,'
                    'latest_version.version '
                    'from Asset where versions.task.id is {} and type.id is {}'.format(
                        context_id, asset_type_entity['id']
                    )
                ).all()
            else:
                assets = self.session.query(
                    'select name, versions.task.id, type.id, id, latest_version,'
                    'latest_version.version '
                    'from Asset where parent.id is {} and type.id is {}'.format(
                        context_id, asset_type_entity['id']
                    )
                ).all()
            return sorted(
                list(assets),
                key=lambda a: a['latest_version']['date'],
                reverse=True,
            )
        elif payload['context_type'] == 'asset_version':
            result = []
            for version in self.session.query(
                'select version, id '
                'from AssetVersion where task.id is {} and asset_id is {} order by'
                ' version descending'.format(context_id, payload['asset_id'])
            ).all():
                result.append(version)
            return result
        else:
            raise Exception(
                'Unknown context_type: {}'.format(payload['context_type'])
            )

    def run(self, store):
        '''
        Store location path from the :obj:`self.options['asset_versions']`.

        ['asset_versions']: expected a list of dictionaries
        containing 'asset_version_id' and 'component_name' for the desired
        assets to open.
        '''
        unresolved_asset_messages = []
        collected_paths = []
        asset_versions = self.options.get('asset_versions')
        for asset_version_dict in asset_versions:
            component = self.session.query(
                'select id from Component where version_id is {} '
                'and name is {}'.format(
                    asset_version_dict['asset_version_id'],
                    asset_version_dict['component_name'],
                )
            ).first()
            if not component:
                message = (
                    'Component name {} not available for '
                    'asset version id {}'.format(
                        asset_version_dict['component_name'],
                        asset_version_dict['asset_version_id'],
                    )
                )
                self.logger.warning(message)
                unresolved_asset_messages.append(message)
                continue
            location = self.session.pick_location()
            component_path = location.get_filesystem_path(component)
            collected_paths.append(component_path)
        if not collected_paths:
            self.message = '\n'.join(unresolved_asset_messages)
            self.status = constants.status.ERROR_STATUS

        component_name = self.options.get('component', 'main')
        store['components'][component_name][
            'collected_paths'
        ] = collected_paths
