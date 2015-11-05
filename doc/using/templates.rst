..
    :copyright: Copyright (c) 2015 ftrack

.. _using/templates:

*****************
Context templates
*****************

Context templates are used to define the hierarchy to generate in ftrack
when exporting from Nuke Studio. The plugin comes with a set of default
templates. To read more about how they are used see
:ref:`Exporting a project <using/export_project>`. Below is a list of available
default templates:

==========================  ====================
Template                    Description
==========================  ====================
Classic, sequence and shot  Match `SQ` or `SH` and any subsequent numbers. Example: `SQ001_SH010` will be matched as Sequence with name `001` and a shot named `010`.
Classic, shot only          Match `SH` and any subsequent digits. Example: `vfx_SH001` will match `001`.
Full name, shot only        Match entire clip name. Example: `vfx_SH001` will match `vfx_SH001`.
==========================  ====================

.. seealso::

    :ref:`Adding your own templates <developing/adding_custom_templates>`