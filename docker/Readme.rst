# :copyright: Copyright (c) 2018 ftrack

Docker for building ftrack-connect-package
==========================================

For Windows and Linux dockers are available to sanbox the build process.

Build:
------

Windows
.......

.. code::cmd

   docker build -t ftrack/connect-package:win10 -f Win10-Dockerfile .


Linux C7
........

.. code::bash

    docker build -t ftrack/connect-package:c7 -f C7-Dockerfile .


Linux C8
........

.. code::bash

    docker build -t ftrack/connect-package:c8 -f C8-Dockerfile .


Run 
---

.. code::bash

    docker run ftrack/connect-package:<TAG>


Extract builds
--------------

Get last container id with: docker ps -a
and get the latest CONTAINER ID number.


Windows
.......

.. code::bash

    docker cp <container-id>:/usr/src/app/ftrack-connect-package/dist/ftrack-connect-package-2.0-amd64.msi


Linux C7
........

.. code::bash
    
    docker cp <container-id>:/usr/src/app/ftrack-connect-package/build/ftrack-connect-2-C7.tar.gz .


Linux C8
........

.. code::bash

    docker cp <container-id>:/usr/src/app/ftrack-connect-package/build/ftrack-connect-2-C8.tar.gz .
