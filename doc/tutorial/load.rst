..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/load:

*******************************
Load camera image plane in Maya
*******************************

.. highlight:: bash

Next, we implement a custom camera loader within Maya that loads a reviewable Quicktime
(.mov) as an image plane, to aid animation and lighting.

Constrain camera loader
***********************

As a preparation, we constrain the camera loader to only bee seen when on animation
and lighting tasks, hiding it during modeling. We do this by modifying the loader
definition json:

**definitions/loader/maya/camera-maya-loader.json**

.. code-block:: json

    {
        "type": "loader",
        "name": "Camera Loader",
        "asset_type": "cam",
        "host_type": "maya",
        "ui_type": "qt",
        "discoverable": ["animation","lighting"]
    }

Here we have added the additional *discoverable* key with associate task type names.


Image sequence loader
*********************

This serves as an example on how to implement your own loader that is not part of
the framework but required in production.

Loading a plate onto an existing camera image plane is great to have when framing
the animation.

Reviewable Quicktimes are most likely published with image sequences (asset type), from Nuke
Studio or similar tool. This is why we implement an new *image sequence loader*:

**definitions/loader/maya/image-sequence-maya-loader.json**


