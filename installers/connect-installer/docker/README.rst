# :copyright: Copyright (c) 2014-2023 ftrack

Docker for building ftrack-connect-installer
==========================================

For Windows and Linux dockers are available to sanbox the build process.

Build:
------

.. note::

   If you are building on desktop and not on CI it is suggested to add the flag --no-cache to ensure no previous cache is used.


Windows
.......

.. note::

    In order to run windows containers, is required windows **10 professional** or above.


.. code-block::

   docker build --rm -t ftrack/connect-package:win10 -f Win10.Dockerfile .


Linux C7
........

.. code-block::

    docker build --rm -t ftrack/connect-package:c7 -f C7.Dockerfile .


Linux C8
........

.. code-block::

    docker build --rm -t ftrack/connect-package:c8 -f C8.Dockerfile .


Run 
---

.. note::

    The image has to **run** a first time before extracting the built result.


.. code-block::

    docker run ftrack/connect-package:<TAG>


Extract builds
--------------

To get the latest **CONTAINER ID** number.

.. code-block::

    docker ps -l



Windows
.......

.. code-block::

    docker cp CONTAINER ID:"/usr/src/app/ftrack-connect-installer/dist/ftrack Connect-2.0.0-win64.msi" .


Linux C7
........

.. code-block::

    docker cp CONTAINER ID:"/usr/src/app/ftrack-connect-installer/build/ftrack Connect-2.0-C7.tar.gz" .


Linux C8
........

.. code-block::

    docker cp CONTAINER ID:"/usr/src/app/ftrack-connect-installer/build/ftrack Connect-2.0-C8.tar.gz" .


Debug
-----


To inspect the docker run :

.. code-block::

    docker run -ti CONTAINER ID bash/cmd


