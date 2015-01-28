..
    :copyright: Copyright (c) 2014 ftrack

Known Bugs
**********

There's a set of known bug in Nuke Studio which are directly affecting this tool:

* **#46660** : rejecting a tag drop through the handler
    this will be allowing double tagging of the clips , which breaks the project cretion

* **#40782** : getting project default settings
    found a workaround for this for the time being

* **#46254** : tags added through python are not editable
    this won’t allow the tag’s regular expressions to be customized before the drop

* **#46256** : not easy to change the project name
    this will be just annoying for the end user to change the project name within NukeStudio
