# :copyright: Copyright (c) 2020 ftrack

Docker for building ftrack-connect-package
==========================================

For Windows and Linux dockers are available to sanbox the build process.

Build:
------

Windows
.......

.. note::

    In order to run windows containers, is required windows 10 professional or above.

.. code-block::

   docker build -t ftrack/connect-package:win10 -f Win10-Dockerfile .


Linux C7
........

.. code-block::

    docker build -t ftrack/connect-package:c7 -f C7-Dockerfile .


Linux C8
........

.. code-block::

    docker build -t ftrack/connect-package:c8 -f C8-Dockerfile .


Run 
---

.. code-block::

    docker run ftrack/connect-package:<TAG>


Extract builds
--------------

Get last container id with: docker ps -a
and get the latest CONTAINER ID number.


Windows
.......

.. code-block::

    docker cp <container-id>:/usr/src/app/ftrack-connect-package/dist/ftrack-connect-package-2.0-amd64.msi


Linux C7
........

.. code-block::

    docker cp <container-id>:/usr/src/app/ftrack-connect-package/build/ftrack-connect-2-C7.tar.gz .


Linux C8
........

.. code-block::

    docker cp <container-id>:/usr/src/app/ftrack-connect-package/build/ftrack-connect-2-C8.tar.gz .
