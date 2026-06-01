# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

"""Factory to create ftrack task exporters with minimal boilerplate.

This factory dramatically reduces code duplication by automatically
generating Task, Preset, and UI classes using the mixin pattern.

Example:
    >>> from hiero.exporters.FnCopyExporter import CopyExporter, CopyPreset
    >>> from hiero.exporters.FnCopyExporterUI import CopyExporterUI
    >>>
    >>> FtrackCopyExporter, FtrackCopyExporterPreset, FtrackCopyExporterUI = create_ftrack_task(
    ...     base_exporter_class=CopyExporter,
    ...     base_preset_class=CopyPreset,
    ...     base_ui_class=CopyExporterUI,
    ...     component_name='Ingest',
    ...     component_pattern='.%d.{ext}',
    ...     asset_type_name='Image Sequence',
    ...     display_name='Ftrack Copy Exporter',
    ...     custom_resolvers=[
    ...         ('{ext}', 'Extension of the file', lambda k, t: t.fileext())
    ...     ]
    ... )
"""

from ftrack_nuke_studio.mixins import (
    FtrackTaskMixin,
    FtrackPresetMixin,
    FtrackUIMixin,
)
from ftrack_nuke_studio.factory.resolver_utils import add_standard_resolvers
from ftrack_nuke_studio.config import report_exception


def create_ftrack_task(
    base_exporter_class,
    base_preset_class,
    base_ui_class,
    component_name,
    component_pattern,
    asset_type_name,
    display_name=None,
    custom_resolvers=None,
    custom_init=None,
    custom_preset_init=None,
    include_thumbnail=False,
    include_reviewable=False,
):
    """Factory to create ftrack task exporters with minimal boilerplate.

    This function generates three classes (Task, Preset, UI) that use
    mixins for ftrack functionality, eliminating ~130 lines of boilerplate
    per exporter.

    Args:
        base_exporter_class: Hiero exporter class (e.g., CopyExporter)
        base_preset_class: Hiero preset class (e.g., CopyPreset)
        base_ui_class: Hiero UI class (e.g., CopyExporterUI)
        component_name: Default component name (e.g., 'Ingest')
        component_pattern: File pattern (e.g., '.%d.{ext}')
        asset_type_name: Default asset type (e.g., 'Image Sequence')
        display_name: Display name in UI (optional, defaults to 'Ftrack {component_name}')
        custom_resolvers: List of (token, description, fn) tuples (optional)
        custom_init: Custom initialization function for task (optional)
        custom_preset_init: Custom initialization function for preset (optional)
        include_thumbnail: Whether to include thumbnail option in UI (default False)
        include_reviewable: Whether to include reviewable option in UI (default False)

    Returns:
        Tuple of (TaskClass, PresetClass, UIClass)

    Example:
        >>> # Create all three classes with ~20 lines instead of ~150
        >>> MyExporter, MyPreset, MyUI = create_ftrack_task(
        ...     base_exporter_class=CopyExporter,
        ...     base_preset_class=CopyPreset,
        ...     base_ui_class=CopyExporterUI,
        ...     component_name='MyComponent',
        ...     component_pattern='.####.exr',
        ...     asset_type_name='Render',
        ...     display_name='My Custom Exporter'
        ... )
        >>>
        >>> # Register with Hiero
        >>> hiero.core.taskRegistry.registerTask(MyPreset, MyExporter)
        >>> hiero.ui.taskUIRegistry.registerTaskUI(MyPreset, MyUI)
    """

    # === Task Class ===
    class FtrackTask(FtrackTaskMixin, base_exporter_class):
        """Generated ftrack task class.

        This class combines FtrackTaskMixin (for ftrack functionality)
        with the Hiero base exporter class.
        """

        @report_exception
        def __init__(self, init_dict):
            """Initialize task.

            Args:
                init_dict: Hiero task initialization dict
            """
            # Initialize base exporter
            base_exporter_class.__init__(self, init_dict)

            # Initialize ftrack mixin (composition)
            self.__init_ftrack__(init_dict, self._preset.properties())

            # Custom initialization if provided
            if custom_init:
                custom_init(self, init_dict)

    # === Preset Class ===
    class FtrackTaskPreset(FtrackPresetMixin, base_preset_class):
        """Generated ftrack preset class.

        This class combines FtrackPresetMixin (for ftrack functionality)
        with the Hiero base preset class.
        """

        @report_exception
        def __init__(self, name, properties):
            """Initialize preset.

            Args:
                name: Preset name
                properties: Preset properties dict
            """
            # Initialize base preset
            base_preset_class.__init__(self, name, properties)

            # Initialize ftrack mixin (composition)
            self.__init_ftrack__(name, properties)

            # Set parent type
            self._parentType = FtrackTask

            # Update with provided properties
            self.properties().update(properties)

            # Set name to component name
            if "ftrack" in self.properties():
                self.setName(self.properties()["ftrack"]["component_name"])

            # Custom preset initialization
            if custom_preset_init:
                custom_preset_init(self, name, properties)

        def name(self):
            """Return component name.

            Returns:
                Component name from ftrack properties
            """
            return self.properties()["ftrack"]["component_name"]

        def set_ftrack_properties(self, properties):
            """Set ftrack-specific properties.

            Args:
                properties: Properties dict to update
            """
            # Call parent to set common properties
            super().set_ftrack_properties(properties)

            # Set task-specific properties
            properties["ftrack"]["component_name"] = component_name
            properties["ftrack"]["component_pattern"] = component_pattern
            properties["ftrack"]["asset_type_name"] = asset_type_name
            properties["ftrack"]["task_id"] = hash(self.__class__.__name__)

        def addUserResolveEntries(self, resolver):
            """Add token resolvers.

            Args:
                resolver: Hiero resolver object
            """
            # Add ftrack resolvers
            self.addFtrackResolveEntries(resolver)

            # Add standard resolvers (clip, shot, track, sequence)
            add_standard_resolvers(resolver)

            # Add custom resolvers if provided
            if custom_resolvers:
                for token, description, fn in custom_resolvers:
                    resolver.addResolver(token, description, fn)

    # === UI Class ===
    class FtrackTaskUI(FtrackUIMixin, base_ui_class):
        """Generated ftrack UI class.

        This class combines FtrackUIMixin (for ftrack UI widgets)
        with the Hiero base UI class.
        """

        @report_exception
        def __init__(self, preset):
            """Initialize UI.

            Args:
                preset: Task preset
            """
            # Initialize base UI
            base_ui_class.__init__(self, preset)

            # Set display properties
            self._displayName = display_name or f"Ftrack {component_name}"
            self._taskType = FtrackTask

        def populateUI(self, widget, exportTemplate):
            """Populate UI with widgets.

            Args:
                widget: Parent QWidget
                exportTemplate: Export template
            """
            # Base UI
            base_ui_class.populateUI(self, widget, exportTemplate)

            # Add ftrack UI section
            self.add_ftrack_ui_section(
                widget,
                include_thumbnail=include_thumbnail,
                include_reviewable=include_reviewable,
            )

    # Return all three generated classes
    return FtrackTask, FtrackTaskPreset, FtrackTaskUI
