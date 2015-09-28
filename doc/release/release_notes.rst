..
    :copyright: Copyright (c) 2014 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: Upcoming
    
    .. change:: changed

        Store reference to outermost ftrack entity in hierarchy when exporting
        track items.

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
