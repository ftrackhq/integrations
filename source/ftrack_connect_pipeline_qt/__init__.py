from ._version import __version__

from ftrack_connect_pipeline.configure_logging import configure_logging
configure_logging(__name__, extra_modules=['ftrack_connect_pipeline'])
