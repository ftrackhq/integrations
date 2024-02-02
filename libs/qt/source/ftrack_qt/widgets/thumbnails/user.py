# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
# TODO: Clean this code

import urllib.request, urllib.parse, urllib.error

from ftrack_qt.widgets.thumbnails.ellipse import EllipseThumbnailBase


class UserThumbnail(EllipseThumbnailBase):
    '''User(avatar) thumbnail widget'''

    def _download(self, reference):
        '''Return thumbnail from *reference*.'''
        thumbnail = self.session.query(
            'select thumbnail from User where username is "{}"'.format(
                reference
            )
        ).first()['thumbnail']
        url = self.get_thumbnail_url(thumbnail)
        return super(UserThumbnail, self)._download(url)

    def get_thumbnail_url(self, component):
        if not component:
            return

        params = urllib.parse.urlencode(
            {
                'id': component['id'],
                'username': self.session.api_user,
                'apiKey': self.session.api_key,
            }
        )

        result_url = '{base_url}/component/thumbnail?{params}'.format(
            base_url=self.session._server_url, params=params
        )
        return result_url
