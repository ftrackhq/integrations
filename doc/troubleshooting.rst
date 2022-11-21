..
    :copyright: Copyright (c) 2022 ftrack

.. _troubleshooting:

***************
Troubleshooting
***************

.. list-table:: Common issues:
   :widths: 25 75
   :header-rows: 1

   * - ISSUE
     - SOLUTION
   * - I see no DCC app launchers when running action in ftrack / Connect.
     - Make sure: 1) Connect is running and all integration dependency plugins are found, either in default location or where FTRACK_CONNECT_PLUGIN_PATH points. Also make sure there are no duplicates. 2) Make sure you have installed DCC app in default location, or update the search location in ftrack-application-launcher/config. 3) Make sure you have built the Framework using the Python interpreter version supported by the DCC app (either Py 3.7 or Py 2.7 for older versions).
   * - The ftrack menu is not showing within DCC.
     - Make sure you are running a Python 3 enabled DCC application, or a Python 2 enabled if you have built the Framework for Python 2.
   * - My DCC is running a newer incompatible Python 3 interpreter.
     - You will need to rebuild the framework plugins with that Python version and launch Connect with FTRACK_CONNECT_PLUGIN_PATH pointing to the collected builds folder.
   * - I am getting a traceback/exception with the DCC that I cannot interpret.
     - If the exception happens within the ftrack Framework and not within your custom code, feel free to reach out to support@ftrack.com and describe the issue together with supplied logs and other useful information.



