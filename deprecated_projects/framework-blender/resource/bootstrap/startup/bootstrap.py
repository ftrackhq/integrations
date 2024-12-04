# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack
import logging

logger = logging.getLogger(__name__)


def register():
    import sys
    import os
    import site

    ext_libs = os.environ.get("FRAMEWORK_DEPENDENCIES")
    if ext_libs and os.path.exists(ext_libs):
        if ext_libs not in sys.path:
            logger.debug(
                "Added path from FRAMEWORK_DEPENDENCIES: %s" % ext_libs
            )
            site.addsitedir(ext_libs)

    import ftrack_framework_blender


def unregister():
    pass


if __name__ == "__main__":
    register()
