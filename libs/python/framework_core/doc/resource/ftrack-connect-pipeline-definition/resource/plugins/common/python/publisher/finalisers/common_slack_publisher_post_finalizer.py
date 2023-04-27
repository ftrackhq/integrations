# :coding: utf-8
# :copyright: Copyright (c) 2014-2022 ftrack
import os

from slack import WebClient

import ftrack_api

from ftrack_connect_pipeline import plugin


class CommonSlackPublisherFinalizerPlugin(plugin.PublisherPostFinalizerPlugin):

    plugin_name = 'common_slack_publisher_finalizer'

    SLACK_CHANNEL = 'test'

    def run(self, context_data=None, data=None, options=None):

        # Harvest publish data
        reviewable_path = asset_version_id = component_names = None
        for component_data in data:
            if component_data['name'] == 'thumbnail':
                for output in component_data['result']:
                    if output['name'] == 'exporter':
                        reviewable_path = output['result'][0]['result'][0]
            elif component_data['type'] == 'finalizer':
                for step in component_data['result']:
                    if step['name'] == 'finalizer':
                        asset_version_id = step['result'][0]['result'][
                            'asset_version_id'
                        ]
                        component_names = step['result'][0]['result'][
                            'component_names'
                        ]
                        break

        # Fetch version
        version = self.session.query(
            'AssetVersion where id={}'.format(asset_version_id)
        ).one()

        # Fetch path to thumbnail
        if reviewable_path:
            # Assume it is on the form /tmp/tmp7vlg8kv5.jpg.0000.jpg, locate our copy
            reviewable_path = os.path.join(
                os.path.dirname(reviewable_path),
                'slack-{}'.format(os.path.basename(reviewable_path)),
            )

        client = WebClient("<slack-api-key>")

        ident = '|'.join(
            [cl['name'] for cl in version['asset']['parent']['link']]
            + [version['asset']['name'], 'v%03d' % (version['version'])]
        )

        if reviewable_path:
            self.logger.info(
                'Posting Slack message "{}" to channel {}, attaching reviewable "{}"'.format(
                    ident, self.SLACK_CHANNEL, reviewable_path
                )
            )
            try:
                response = client.files_upload(
                    channels=self.SLACK_CHANNEL,
                    file=reviewable_path,
                    title=ident,
                    initial_comment=version['comment'],
                )
            finally:
                os.remove(reviewable_path)  # Not needed anymore
        else:
            # Just post a message
            self.logger.info(
                'Posting Slack message "{}" to channel {}, without reviewable'.format(
                    ident, self.SLACK_CHANNEL
                )
            )
            client.chat_postMessage(channel=self.SLACK_CHANNEL, text=ident)
        if response.get('ok') is False:
            raise Exception(
                'Slack file upload failed! Details: {}'.format(response)
            )

        return {}


def register(api_object, **kw):
    if not isinstance(api_object, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return
    plugin = CommonSlackPublisherFinalizerPlugin(api_object)
    plugin.register()
