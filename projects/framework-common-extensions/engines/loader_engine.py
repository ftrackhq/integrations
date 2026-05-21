# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack


from ftrack_framework_core.engine import BaseEngine
from ftrack_framework_loader import constants as loader_const


class LoaderEngine(BaseEngine):
    """
    Loader Engine that orchestrates asset loading operations.

    The loader pipeline consists of multiple stages:
    1. Context - validate/prepare context
    2. For each component to load:
       a. Collector - collect component paths from ftrack
       b. Importer - create tracking nodes and/or load DCC content
       c. Post Importer - post-import operations
    3. Pre Finalizer - pre-finalization operations
    4. Finalizer - finalization operations
    5. Post Finalizer - post-finalization operations
    """

    name = "loader_engine"
    engine_types = ["loader"]

    def __init__(
        self,
        plugin_registry,
        session,
        context_id=None,
        on_plugin_executed=None,
    ):
        """
        Initialize LoaderEngine with *plugin_registry*, *session*,
        *context_id* and *on_plugin_executed* callback.
        """
        super(LoaderEngine, self).__init__(
            plugin_registry,
            session,
            context_id,
            on_plugin_executed=on_plugin_executed,
        )

    def get_store(self):
        """Return initial store dictionary for loader pipeline"""
        return {
            "context_id": self.context_id,
            loader_const.STORE_CONTEXT_DATA: {},
            loader_const.STORE_COLLECTED_PATHS: [],
            loader_const.STORE_COMPONENT_RESULTS: {},
            loader_const.STORE_RESULTS: {},
        }

    def run(self, data):
        """
        Execute the loader pipeline with given *data*.

        *data* should contain:
        - method: One of 'init_nodes', 'load_asset', 'init_and_load', or 'run'
        - tool_config: The loader tool configuration
        - context_data: Context information (version_id, etc.)
        - selected_components: List of component names to load (optional)
        - options: Additional options (load_mode, load_options, etc.)

        Returns store dict with results.
        """
        method = data.get("method", loader_const.METHOD_INIT_AND_LOAD)
        tool_config = data.get("tool_config")
        context_data = data.get("context_data", {})
        selected_components = data.get("selected_components", [])
        global_options = data.get("options", {})

        if not tool_config:
            raise ValueError("tool_config is required in data")

        store = self.get_store()
        store[loader_const.STORE_CONTEXT_DATA] = context_data

        self.logger.info(
            f"Running loader pipeline with method: {method}, "
            f"selected components: {selected_components}"
        )

        try:
            # Stage 1: Context
            self._run_context_stage(tool_config, store, global_options)

            # Stage 2-4: Process each selected component
            components = tool_config.get("components", [])
            for component_config in components:
                component_name = component_config.get(
                    loader_const.COMPONENT_NAME
                )

                # Skip if component list specified and this isn't in it
                if (
                    selected_components
                    and component_name not in selected_components
                ):
                    self.logger.debug(
                        f"Skipping component {component_name} - not selected"
                    )
                    continue

                # Skip if component not selected by default and no override
                if not selected_components:
                    if not component_config.get(
                        loader_const.COMPONENT_SELECTED, True
                    ):
                        self.logger.debug(
                            f"Skipping component {component_name} - not selected by default"
                        )
                        continue

                self.logger.info(f"Processing component: {component_name}")

                # Build component-specific data
                component_data = {
                    "component_name": component_name,
                    "file_formats": component_config.get(
                        loader_const.COMPONENT_FILE_FORMATS, []
                    ),
                }

                # Merge global options with component options
                component_options = dict(global_options)

                # Run component pipeline
                component_result = self._run_component_pipeline(
                    component_config,
                    component_data,
                    component_options,
                    method,
                    store,
                )

                # Store component result
                store[loader_const.STORE_COMPONENT_RESULTS][component_name] = (
                    component_result
                )

            # Stage 5-7: Finalizers
            self._run_finalizer_stages(tool_config, store, global_options)

            self.logger.info("Loader pipeline completed successfully")

        except Exception as error:
            self.logger.exception(f"Loader pipeline failed: {error}")
            store[loader_const.STORE_RESULTS]["status"] = "error"
            store[loader_const.STORE_RESULTS]["message"] = str(error)
            raise

        return store

    def _run_context_stage(self, tool_config, store, options):
        """Execute context stage plugins"""
        context_plugins = tool_config.get("context", [])

        for plugin_config in context_plugins:
            plugin_name = plugin_config.get("plugin")
            plugin_options = plugin_config.get("options", {})
            plugin_options.update(options)

            self.logger.debug(f"Running context plugin: {plugin_name}")
            self.run_plugin(
                plugin_name,
                store,
                plugin_options,
                reference=f"context.{plugin_name}",
            )

    def _run_component_pipeline(
        self, component_config, component_data, options, method, store
    ):
        """
        Execute the component loading pipeline.

        Returns result dict with component load results.
        """
        component_name = component_data["component_name"]
        component_result = {
            "status": "unknown",
            "collector_result": None,
            "importer_result": None,
            "post_importer_result": None,
        }

        # Get plugins for this component
        component_plugins = component_config.get(
            loader_const.COMPONENT_PLUGINS, []
        )

        # Group plugins by stage
        collector_plugins = [
            p
            for p in component_plugins
            if p.get("stage") == loader_const.STAGE_COLLECTOR
        ]
        importer_plugins = [
            p
            for p in component_plugins
            if p.get("stage") == loader_const.STAGE_IMPORTER
        ]
        post_importer_plugins = [
            p
            for p in component_plugins
            if p.get("stage") == loader_const.STAGE_POST_IMPORTER
        ]

        # Create component store
        component_store = {
            "component_data": component_data,
            "context_data": store[loader_const.STORE_CONTEXT_DATA],
        }

        try:
            # Stage 2: Collector - collect component paths from ftrack
            for plugin_config in collector_plugins:
                plugin_name = plugin_config.get("name")
                plugin_options = plugin_config.get("options", {})
                plugin_options.update(options)

                self.logger.debug(
                    f"Running collector plugin: {plugin_name} for component {component_name}"
                )
                self.run_plugin(
                    plugin_name,
                    component_store,
                    plugin_options,
                    reference=f"collector.{component_name}.{plugin_name}",
                )

            component_result["collector_result"] = component_store.get(
                "result"
            )

            # Stage 3: Importer - create tracking nodes and/or load content
            for plugin_config in importer_plugins:
                plugin_name = plugin_config.get("name")
                plugin_options = plugin_config.get("options", {})
                plugin_options.update(options)
                plugin_options["method"] = method  # Pass method to plugin

                self.logger.debug(
                    f"Running importer plugin: {plugin_name} for component {component_name} with method {method}"
                )
                self.run_plugin(
                    plugin_name,
                    component_store,
                    plugin_options,
                    reference=f"importer.{component_name}.{plugin_name}",
                )

            component_result["importer_result"] = component_store.get("result")

            # Stage 4: Post Importer - post-import operations
            for plugin_config in post_importer_plugins:
                plugin_name = plugin_config.get("name")
                plugin_options = plugin_config.get("options", {})
                plugin_options.update(options)

                self.logger.debug(
                    f"Running post_importer plugin: {plugin_name} for component {component_name}"
                )
                self.run_plugin(
                    plugin_name,
                    component_store,
                    plugin_options,
                    reference=f"post_importer.{component_name}.{plugin_name}",
                )

            component_result["post_importer_result"] = component_store.get(
                "result"
            )

            component_result["status"] = "success"

        except Exception as error:
            self.logger.exception(
                f"Component pipeline failed for {component_name}: {error}"
            )
            component_result["status"] = "error"
            component_result["message"] = str(error)

        return component_result

    def _run_finalizer_stages(self, tool_config, store, options):
        """Execute finalizer stage plugins"""
        finalizers = tool_config.get("finalizers", [])

        for finalizer_config in finalizers:
            stage_name = finalizer_config.get("name")
            plugin_name = finalizer_config.get("plugin")
            plugin_options = finalizer_config.get("options", {})
            plugin_options.update(options)

            self.logger.debug(
                f"Running finalizer: {plugin_name} ({stage_name})"
            )
            self.run_plugin(
                plugin_name,
                store,
                plugin_options,
                reference=f"finalizer.{stage_name}.{plugin_name}",
            )
