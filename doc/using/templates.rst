..
    :copyright: Copyright (c) 2015 ftrack

.. _using/templates:

*****************
Context templates
*****************

Context templates are used to define the hierarchy to generate in ftrack
when exporting from Nuke Studio. The plugin comes with a set of default
templates. Below is a list of available
default templates:

==========================  ====================
Template                    Description
==========================  ====================
Basic, sequence and shot    Match splitting by _. Example: `SQ001_SH010` will be matched as Sequence with name `SQ001` and a shot named `SH010`.
Classic, sequence and shot  Match `SQ` or `SH` and any subsequent numbers. Example: `SQ001_SH010` will be matched as Sequence with name `001` and a shot named `010`.
Classic, shot only          Match `SH` and any subsequent digits. Example: `vfx_SH001` will match `001`.
Full name, shot only        Match entire clip name. Example: `vfx_SH001` will match `vfx_SH001`.
==========================  ====================

.. seealso::

    :ref:`Adding your own templates <developing/adding_custom_templates>`