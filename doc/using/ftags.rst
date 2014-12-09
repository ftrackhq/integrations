ftags
*****

A new tools has been made available to simplify the creation of the project
from within Nuke Studio. This tool rely on a new set of tags, made for ftrack.

FTags are custom tags, created in order to connect your clips to context in ftack.

.. image:: /image/ftags.png


context
=======

Context tags, act as reference for the context location into the ftrack project.
Each of the following tags will map to an ftrack's project entity.

* **project**
* **episode**
* **sequence**
* **shot**

These tags are special, as they containing the logic to extract the relevant informations from the clip name.
This logic is expressed through a regular expression which will be taking care of extracting the values.

.. image:: /image/ftag.png

.. note::
    Eg: the episode's tag, will be using the regular expression (\w+.)?EP(\d+) to match EP001_SH005 end extract the value of 001
    where the shot one will be using (\w+.)?SH(\d+) to extract 005 from the same clip name.

    .. image:: /image/regex.png

    .. note::
        Project is a special one, and will be extracting the value from the Nuke Studio's project name.

    .. warning::
        Due to a known bug the tag's regular expression can't be changed from within the interface.

tasks
=====

These tags are generated from the common and custom tasks available from within the ftrack server.
Once dropped on the clips these will be defining the tasks available for the shot.

.. warning::
    Not all the listed task tags will be actually applied during the project creation. This depend on whether the task is available in the chosen workflow.
    In case of unavailable task, this will be marked as red during the shot creation.
