# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

from ftrack_framework_loader.plugins.base_loader_context import (
    LoaderContextPlugin,
)


class CommonLoaderAssetPickerPlugin(LoaderContextPlugin):
    """
    Loader asset/version picker plugin.

    Pairs with the ``asset_version_selector`` UI widget at the dialog level:
    the ``ui_hook`` returns every AssetVersion (and its components) that
    matches the loader's ``asset_type_name`` for the current context, so the
    dialog can compute per-component loadability and asset_type after the
    user picks a version.

    No store mutation in ``run()`` — the dialog routes the selected
    ``asset_version_id`` onto each enabled component group's collector via
    ``set_tool_config_option``.
    """

    name = "common.loader_asset_picker"

    def ui_hook(self, payload):
        """
        Return the AssetVersions available for the picker.

        *payload* keys:
        - context_id: Current Task (or other Context) id.
        - asset_type_name: AssetType short code to filter by; if falsy, the
          query is unfiltered by type.
        - show_all: If True, broaden scope to the context parent's children
          (mirrors the opener's task-vs-task-parent toggle).

        Return shape matches ``OpenAssetSelector.set_assets()``: a dict with
        an ``assets`` key mapping asset_id -> {name, versions: [...],
        server_url}. Each version carries id, version, date,
        is_latest_version, thumbnail, user, and the component list (name +
        id + location names) so the dialog can render rows without an extra
        round-trip.
        """
        context_id = payload["context_id"]
        asset_type_name = payload.get("asset_type_name")
        show_all = payload.get("show_all")

        context = self.session.get("Context", context_id)
        if not context:
            return {"assets": {}}

        select_clause = (
            "select asset.name, asset.type.short, asset_id, id, date, "
            "version, is_latest_version, thumbnail_url, user.first_name, "
            "user.last_name, components.name, components.id, "
            "components.file_type, "
            "components.component_locations.location.name "
            "from AssetVersion"
        )

        clauses = []
        if context.entity_type == "Task" and not show_all:
            clauses.append(f"task_id is {context_id}")
        elif context.entity_type == "Task" and show_all:
            clauses.append(f"asset.parent.children.id is {context_id}")
        else:
            clauses.append(f"asset.parent.id is {context_id}")

        if asset_type_name:
            asset_type_entity = self.session.query(
                'select id from AssetType where short is "{}"'.format(
                    asset_type_name
                )
            ).first()
            if asset_type_entity:
                clauses.append(f'asset.type.id is {asset_type_entity["id"]}')

        query = "{} where {}".format(select_clause, " and ".join(clauses))
        asset_versions = self.session.query(query).all()

        result = {"assets": {}}
        with self.session.auto_populating(False):
            for asset_version in asset_versions:
                asset_id = asset_version["asset_id"]
                if asset_id not in result["assets"]:
                    result["assets"][asset_id] = {
                        "name": asset_version["asset"]["name"],
                        "versions": [],
                        "server_url": self.session.server_url,
                    }

                components = []
                for component in asset_version["components"]:
                    location_names = [
                        cl["location"]["name"]
                        for cl in component["component_locations"]
                    ]
                    components.append(
                        {
                            "id": component["id"],
                            "name": component["name"],
                            "file_type": component.get("file_type"),
                            "location_names": location_names,
                        }
                    )

                asset_type_short = None
                asset_entity = asset_version.get("asset")
                if asset_entity:
                    asset_type_entity = asset_entity.get("type")
                    if asset_type_entity:
                        asset_type_short = asset_type_entity.get("short")

                result["assets"][asset_id]["versions"].append(
                    {
                        "id": asset_version["id"],
                        "date": asset_version["date"].strftime(
                            "%y-%m-%d %H:%M"
                        ),
                        "version": asset_version["version"],
                        "is_latest_version": asset_version[
                            "is_latest_version"
                        ],
                        "thumbnail": asset_version["thumbnail_url"]["url"],
                        "user_first_name": asset_version["user"]["first_name"],
                        "user_last_name": asset_version["user"]["last_name"],
                        "asset_type": asset_type_short,
                        "components": components,
                    }
                )
        return result

    def run(self, store):
        """No-op: the dialog routes asset_version_id to each collector."""
        self.logger.debug(
            "loader_asset_picker run() — no store mutation; "
            "dialog drives per-collector asset_version_id."
        )
        store["result"] = {"status": "success"}
        return store["result"]


def register(api_object, **kw):
    """Register plugin to framework"""
    # Auto-registration handled by framework plugin discovery
    pass
