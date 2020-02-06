from ._version import __version__

from ftrack_connect_pipeline.configure_logging import configure_logging
configure_logging('ftrack_connect_pipeline_qt', extra_modules=['python_jsonschema_objects'])
