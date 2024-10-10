# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack


def register():
    import sys
    import os
    import site

    # print("hello world")
    # print(f"PATH --> {os.environ.get('PATH')}")
    # print(f"PYTHONPATH --> {os.environ.get('PYTHONPATH')}")
    # print(f"BLENDER_USER_SCRIPTS --> {os.environ.get('BLENDER_USER_SCRIPTS')}")
    #
    # ext_libs = os.environ.get("PYTHONPATH")
    # if ext_libs and os.path.exists(ext_libs):
    #     if ext_libs not in sys.path:
    #         print("Added path: %s" % ext_libs)
    #         site.addsitedir(ext_libs)
    # ext_libs = os.environ.get("BLENDER_USER_SCRIPTS")
    # if ext_libs and os.path.exists(ext_libs):
    #     if ext_libs not in sys.path:
    #         print("Added path: %s" % ext_libs)
    #         site.addsitedir(ext_libs)
    # from PySide6 import QtWidgets
    # import ftrack_framework_blender
    print("hello world2")

    ext_libs = os.environ.get("PYSIDE6_BLENDER_PATH")
    if ext_libs and os.path.exists(ext_libs):
        if ext_libs not in sys.path:
            print("Added path: %s" % ext_libs)
            site.addsitedir(ext_libs)
    import ftrack_framework_blender


def unregister():
    pass


if __name__ == "__main__":
    register()
#
# def register():
#     print("hello world")
#     import ftrack_framework_blender
#
# def unregister():
#     pass
#
# if __name__ == "__main__":
#     register()
