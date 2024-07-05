import os
import ftrack_api

# https://help.autodesk.com/view/FLAME/2022/ENU/?gugid=Flame_API_Python_Hooks_Reference_Python_Hooks_Tips_html
#    to be used to override the export hook as : bmea
#    sd fxpbmgeasd forter.export(
#        gm clip, preset_path, export_dir, hooks=hooks, hooks_user_data=hooks_user_data
#     )

class FtrackPostRenderhHook(object):

    @property
    def session(self):
        return self._session

    @property
    def asset_type(self):
        return self.session.query(f'AssetType where name is "{self._asset_type_name}"').one()

    @property
    def asset(self):
        parent = self.context['parent']
        asset = self.session.query(
            f'Asset where name is {self._asset_name} and type_id is {self.asset_type["id"]} and parent_id is {parent["id"]}'
        ).first()

        return asset

    @property
    def context(self):
        return self.session.get('Context', self._context_id)

    @property
    def location(self):
        return self._session.pick_location()

    def __init__(self, ftrack_session, context_id, component_name, asset_name, asset_type_name, is_review):
        self._session = ftrack_session
        self._context_id = context_id
        self._component_name = component_name
        self._asset_name = asset_name
        self._asset_type_name = asset_type_name
        self._is_review = is_review

    def postExportAsset(self, info, userData, *args, **kwargs):
        full_path = os.path.join(info["destinationPath"], info["resolvedPath"])
        asset = self.asset
        # check in ftrack db for existing asset....
        if not asset:
            asset = self.session.create('Asset',
                {
                    'name': self._asset_name,
                    'type': self.asset_type,
                    'parent': self.context['parent']
                }
            )

        asset_version = self.session.create('AssetVersion', {
            'asset': asset,
            'task': self.context
        })

        self.session.commit()
        asset_version.create_component(
            full_path, location=self.location
        )
        self.session.commit()

