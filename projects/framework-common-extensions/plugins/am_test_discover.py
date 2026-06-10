# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_core.plugin import BasePlugin


class AssetManagerTestDiscoverPlugin(BasePlugin):
    '''Test discover plugin that returns a filter for discovering assets.'''

    name = 'am_test_discover'

    def run(self, store):
        '''
        Return a discovery filter from :obj:`self.options` or use default
        test values. Store the filter on *store* for downstream use.
        '''
        filter_options = self.options.get('filter', {})

        if not filter_options:
            filter_options = {'asset_name': 'torso', 'asset_type_name': 'geo'}

        self.logger.debug(
            'Asset manager test discover returning filter: {}'.format(
                filter_options
            )
        )

        store['discover_filter'] = filter_options
