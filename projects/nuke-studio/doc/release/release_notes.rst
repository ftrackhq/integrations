..
    :copyright: Copyright (c) 2014 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: Upcoming

    .. change:: fixed
        :tags: Tags

        Tags on sequences break exporters. 

    .. change:: changed
        :tags: Environment Variables

        **HIERO_PLUGIN_PATH** Environment variable is now prepended rather than just set.

.. release:: 2.5.1
    :date: 2022-02-24

    .. change:: changed
        :tags: Setup

        Remove pyside2 installation's dependency. 

    .. change:: changed
        :tags: TaskPlugin
        
        Copy Exporter does not force 4 digit limits in sequence file names.


.. release:: 2.5.0
    :date: 2021-09-06
    
    .. change:: change
        :tags: Discovery

        Update hook for application launcher.
    
    .. change:: change
        :tags: Discovery

        Limit discovery to Nuke 13.+.

    .. change:: change
        :tags: Setup

        Limit to python 3+ version.

    .. change:: change
        :tags: Api
        
        Update to python3 and pyside2.


.. warning::

    From this version the support for ftrack-connect 1.X is dropped, and
    only ftrack-conenct 2.0 will be supported up to the integration EOL.


.. release:: 2.4.1
    :date: 2020-09-15

    .. change:: add
        :tags: Ui

        Startup error related to location setup are now visually reported.

    .. change:: fix
        :tags: Action

        Discovery does break on non context entities.

.. release:: 2.4.0
    :date: 2020-06-17

    .. change:: fixed
        :tags: Track build

        Rebuild track from exported episodes does not work.

    .. change:: change
        :tags: Exporter

        Ensure shot export path is consistent with the location structure generated.

    .. change:: new
        :tags: Exporter

        Add 'Ftrack Copy Exporter' for publish file or sequence to ftrack without transcoding.

    .. change:: fixed
        :tags: Template parser

        Tokens are not always parsed correctly.

    .. change:: change
        :tags: Exporter

        Ensure shot output path normalized when replacing shot name.

    .. change:: change
        :tags: Version

        Replace fixed version with automatic versioning from git repository.
    
    .. change:: fix
        :tags: Exporter

        Reviewable export audio breaks on earlier Nuke Studio versions (version < 12.1).

    .. change:: fix
        :tags: Exporter

        Reviewable Task break when including audio.


.. release:: 2.3.0
    :date: 2020-04-23

    .. change:: fix
        :tags: Internal

        Custom start frame are not consistently output in frame sequence.

    .. change:: change
        :tags: Internal

        Lock OTIO dependency version to last python only.

    .. change:: fix
        :tags: Internal

        Sequences rendered with Nuke Studio cannot be imported in nuke.

    .. change:: fix
        :tags: Internal

        ImageSequences are rendered as FileComponent.

    .. change:: fix
        :tags: Internal

        Thumbnail generation breaks when exporting just nuke scripts.


.. release:: 2.2.5
    :date: 2020-03-12

    .. change:: fix
        :tags: Internal

        Thumbnail generation breaks when setting custom start frame.


.. release:: 2.2.4
    :date: 2020-01-21

    .. change:: changed
        :tags: Setup

        Pip compatibility for version 19.3.0 or higher

    .. change:: Add
        :tags: Internal

        Mark ftrack.perforce-location as non compatible.

    .. change:: fixed
        :tags: Internal

        Replace pyqt with qt.py

.. release:: 2.2.3
    :date: 2019-10-21

    .. change:: fixed
        :tags: Internal

        Improve render task deduplication logic.

    .. change:: fixed
        :tags: Internal

        Integration fails to start on nuke >= 12.

    .. change:: fixed
       :tags: Internal

        Thumbnail frame is now generated from the mid frame of the exported clip.

.. release:: 2.2.2
    :date: 2019-07-10

    .. change:: changed
       :tags: Internal

        Replace QtExt module with QtPy.

.. release:: 2.2.1
    :date: 2019-05-22

    .. change:: fixed

        Tasks are marked as duplicated if the same clip name is present on multiple tracks.

    .. change:: fixed

        Tasks generate empty unwanted components.

    .. change:: changed

        Replace simple EDL export with OpenTimelineIO edl export.

    .. change:: new

        Thumbnails are published also to parent entity.

.. release:: 2.2.0
    :date: 2019-03-08

    .. change:: new

        Extend context template to support episodes.

    .. change:: changed

        Application requires a project to start and
        project selection from export is now disabled.

.. release:: 2.1.3
    :date: 2019-02-21

    .. change:: fixed

        Edl Exporter generates empty components.

    .. change:: new
       :tags: Logging

        Better error handling to log.

.. release:: 2.1.2
    :date: 2019-01-17

    .. change:: fixed

        Due to application api changes, the plugin does not work
        in Nuke Studio/Hiero versions >= 11.3v1.

.. release:: 2.1.1
    :date: 2019-01-11

    .. change:: fixed

        Presets are not properly restored between sessions.

    .. change:: fixed

        Components are not collected under one single asset.

.. release:: 2.1.0
    :date: 2018-12-17

    .. change:: new

        Support tokens resolution in component names.

    .. change:: new

        Support multi track export.

    .. change:: fixed

        Hiero under windows does not load templates.

.. release:: 2.0.1
    :date: 2018-11-12

    .. change:: fixed

        Error when trying to validate duplicated components.

.. release:: 2.0.0
    :date: 2018-10-08

    .. change:: new

        Complete re write of the integration as standalone plugin.

        .. seealso::

            :ref:`migration guide <release/migration>`

.. release:: 1.1.2
    :date: 2017-04-27

    .. change:: fixed
       :tags: Crew

        Nuke Studio 11.1 crashes with ftrack integration.

.. release:: 1.1.1
    :date: 2017-12-14

    .. change:: new
       :tags: Logging

       Improved feedback gathering.

.. release:: 1.1.0
    :date: 2017-09-12

    .. change:: fixed
        :tags: Nuke Studio

        Nuke 11 not supported.

.. release:: 1.0.0
    :date: 2017-07-07

    .. change:: fixed
        :tags: macOS

        Occasional errors when running processors. 

    .. change:: fixed
        :tags: Export project

        Show an error dialog if the img asset type does not exist in the server.

    .. change:: new
        :tags: API

        Remove dependencies on the ftrack legacy API where possible

    .. change:: new
        :tags: Template, Structure

        Add new event to allow modification of the template output structure.

        .. seealso::

            :ref:`Updated template tutorial <developing/customise_template_output>`

.. release:: 0.2.7
    :date: 2017-01-11

    .. change:: fixed
        :tags: Custom attributes

        Cannot set custom attributes when used in combination with new api
        and ftrack server version.

.. release:: 0.2.6
    :date: 2016-12-01

    .. change:: changed
        :tags: API

        Switched to require ftrack-python-api > 1.0.0.

.. release:: 0.2.5
    :date: 2016-08-03

    .. change:: fixed
        :tags: Processor

        Processors fail in NukeStudio 10.0v3 and later for single-file track
        items.

.. release:: 0.2.4
    :date: 2016-06-07

    .. change:: fixed
        :tags: Ui

        Schema selection is not in sync with the selected exiting project.

.. release:: 0.2.3
    :date: 2016-05-02

    .. change:: fixed
        :tags: Compatibility

        Plugin doesn't work with Nuke Studio 10.0v1 beta.

.. release:: 0.2.2
    :date: 2016-04-04

    .. change:: fixed
        :tags: Processor

        Handles are not treated correctly when publishing through processors.

.. release:: 0.2.1
    :date: 2016-03-14

    .. change:: changed
        :tags: Processor, Development

        Track item is passed as `application_object` when discovering
        processors.

    .. change:: fixed
        :tags: Create project

        Fix issue where a project cannot be created or updated from the Create
        dialog.

    .. change:: fixed

        Meta data on project is overwritten when an existing project is updated.

.. release:: 0.2.0
    :date: 2015-11-10

    .. change:: new
        :tags: Context template, Context tag

        Introduced :term:`Context templates <Context template>` to simplify
        configuration of project structure on export.

        .. seealso::

            :ref:`Updated export project tutorial <using/export_project>`

        .. note::

            A ftrack server version of 3.3.4 or higher is required.

.. release:: 0.1.4
    :date: 2015-10-16

    .. change:: changed

        Default tag expressions now check for either the previous syntax or
        as-is naming to support a wider variety of use cases out of the box.

        .. note::

            As part of this change the regular expressions must now define a
            "value" named group in order to work.

        .. seealso::

            :ref:`developing/customising_tag_expressions`

    .. change:: changed

        Improved error messages shown when tag expression does not match.

.. release:: 0.1.3
    :date: 2015-10-01

    .. change:: changed

        Propagate thumbnails to tasks on export by default.

        .. seealso::

            :ref:`Thumbnail processor <using/processors/thumbnail>`

    .. change:: changed

        Publish and Proxy processors disabled as default.

    .. change:: changed

        Store reference to outermost ftrack entity in hierarchy when exporting
        track items.

    .. change:: fixed

        Info panel not updating if track item has effect track.

.. release:: 0.1.2
    :date: 2015-09-22

    .. change:: fixed

        Processors not working correct on Windows.

    .. change:: fixed

        Incomplete version number displayed for Nuke Studio application when
        discovered.

    .. change:: fixed

        Changes to context tags hook not being respected.

    .. change:: changed

        Read default export values for `fps` and `resolution` from the
        project settings.

.. release:: 0.1.1
    :date: 2015-09-10

    .. change:: fixed

        Dropping several tags of same type causes export to fail.

    .. change:: fixed

        Segmentation fault when closing down Nuke Studio with plugin loaded.

    .. change:: changed

        Updated default export values for `fps`, `resolution` and `handles`.

    .. change:: fixed
        :tags: Processors, Web playable component

        In and out points not calculated correctly when when offset is used
        on source clip.

.. release:: 0.1.0
    :date: 2015-09-08

    .. change:: new

        Initial release of ftrack connect Nuke studio plugin.
