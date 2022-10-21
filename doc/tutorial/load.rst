..
    :copyright: Copyright (c) 2022 ftrack

.. _tutorial/load:

*******************************
Load camera image plane in Maya
*******************************

Next, we implement a custom loader within Maya. To aid animation, a tracked or
animated camera can be good to have at hand. The new framework comes with a built-in
camera loader. As a part of this customisation guide, we are going to constrain camera
load to be available on only animation and lighting tasks, preventing camera from
being a load option during modeling.

We do this by diving into the ftrack-connect-pipeline-definitions plugin. It has
been designed so pipeline developers can alter the shipped behavior of the new
framework, removing/disable unnecessary loaders/publishers and adding their own.

