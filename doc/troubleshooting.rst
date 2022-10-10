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
     - Make sure: 1) Connect is running and all integration plugins are found, either in default location or where FTRACK_CONNECT_PLUGIN_PATH points. Also make sure no duplicates. 2)Make sure you have installed DCC app in default location, or update the search location in ftrack-application-launcher/config. 3) Make sure you have built the framework using the Python interpreter version supported by DCC app (either Py 3.7 or Py 2.7 for older versions).
   * - TBC
     - TBC


