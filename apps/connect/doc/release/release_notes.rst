
..
    :copyright: Copyright (c) 2014-2023 ftrack

.. _release/release_notes:

*************
Release Notes
*************

.. release:: upcoming

    .. change:: changed

        Convert Object to QObject to ensure proper livecycle handling in pyside.

    .. change:: changed
        :tags: Build system

        Change build system to Poetry, using the monorepo tooling to build QT resources.


.. release:: 2.1.1
    :date: 2023-04-27

    .. change:: fix
        :tags: Plugins

        Limit packaging to prevent crashes on unexpected content in Connect plugin folder.

.. release:: 2.1.0
    :date: 2023-04-05

    .. change:: changed
        :tags: Plugins

        Install all plugins on first launch.

    .. change:: changed
        :tags: Docs

        Update CONTRIBUTING.md to include release notes.

    .. change:: fixed
        :tags: UI

        Application crash on Windows 8.1.
        
    .. change:: fixed
        :tags: API
        
        Ensure all plugin paths are unique.

.. release:: 2.0.1
    :date: 2022-09-01

    .. change:: fixed
        :tags: UX

        Action icons are being cut in task launcher.

    .. change:: fixed
        :tags: UX

        Icons fonts are not correctly loaded during storage setup.

.. release:: 2.0.0
    :date: 2022-07-07

    .. change:: fixed
        :tags: UX

        User's tasks include inactive projects.

    .. change:: changed
        :tags: tray

        Windows and Linux use color icon in system tray.

    .. change:: fixed
        :tags: style

        Variant are highlighted black on light style.

    .. change:: fixed
        :tags: Linux

        Application shortcut points to wrong executable.

    .. change:: fixed
        :tags: UX

        Path with unicode are not rendered spaced correctly.


.. release:: 2.0.0-rc-6
    :date: 2022-06-01

    .. change:: changed
        :tags: Login

        Provide link to get back on logging in through instance address.

    .. change:: changed
        :tags: Style

        Remove play button from action launch and review style.

    .. change:: fixed
        :tags: UX

        Interface expand on long context paths.

    .. change:: fixed
        :tags: Publisher

        Add missing icons and set correct state for drop zone on folders.

    .. change:: fixed
        :tags: Publisher

        Latest published assets are not always refreshing.

    .. change:: changed
        :tags: Style

        Review Dialogs styles.

    .. change:: changed
        :tags: Style

        Review style and icons.

    .. change:: new
        :tags: SystemTray, API

        Allow connect to restart.

    .. change:: changed
        :tags: Plugins

        Remove publisher and launcher from connect codebase.
        Documentation can be found in:

        * :ref:`Publisher documentation <ftrack-connect-publisher-widget:using/publishing>`
        * :ref:`Launcher documentation <ftrack-connect-action-launcher-widget:using/actions>`

    .. change:: changed
        :tags: Codestyle

        Run black pass with flags : black --skip-string-normalization -l 79 . on Codebase.

.. release:: 2.0.0-rc-5
    :date: 2022-03-25

    .. change:: fixed
        :tags: Actions

        Random crashes on discovering on null context.

    .. change:: new
        :tags: Module

        Provide ftrak_connect.qt module to abstract imported Qt modules.
        
    .. change:: changed
        :tags: Events

        Sending of usage_events can now be batched.

    .. change:: changed
        :tags: About, Linux

        Linux Desktop entry respect packaged or virtual environment paths.

    .. change:: changed
        :tags: UX

        Add new icons set for Connect.

    .. change:: changed
        :tags: UX

        Connect color theme respect system theme.

.. release:: 2.0.0-rc-4
    :date: 2022-01-15

    .. change:: changed
        :tags: UX

        Assigned tasks are refreshed on cancel.

    .. change:: changed
        :tags: API

        User's plugin folder is created at startup time.

    .. change:: changed
        :tags: UX

        Context selection is changed to a list of assigned tasks.

    .. change:: new
        :tags: UX

        Indicator during discovery of actions.

    .. change:: new
        :tags: API

        Provide ConnectWidget Plugin with custom name attribute to render.

    .. change:: new
        :tags: API

        Improve ConnectWidget error logging.

    .. change:: new
        :tags: API

        Emit usage data for Connect session duration along version and os type.

    .. change:: fixed
        :tags: API

        Storage scenario help points to dead link.

    .. change:: changed
        :tags: UX

        Provide placeholder text in context selectors.

    .. change:: fixed
        :tags: UX

        Menubar icon smaller on Mac.

    .. change:: changed
        :tags: UX

        Update icon set to use font icons (material/ftrack icons) to ensure full hidpi support.

    .. change:: changed
        :tags: UX

        Consolidate font using Roboto.

    .. change:: changed
        :tags: API

        Remove `ftrack_connect.session` utility class, and `shared_session` usage.

    .. change:: changed
        :tags: Logging

        Improve logging readability.

    .. change:: new
        :tags: API

        Restore ftrack_connect.application module to provide environment variable helper methods.

        .. note::

            We provide for backward compatibility the method **prependPath** and **appendPath**, but these will likely be deprated at a later stage.
            The use of newer methods **prepend_path** and **append_path** in the same module are preferred.


.. release:: 2.0.0-rc-3
    :date: 2021-09-23

    .. change:: changed
        :tags: Setup

        Use latest api release version.

    .. change:: fixed
        :tags: API

        Cannot publish after a failed publish, and need to restart connect.

.. release:: 2.0.0-rc-2
    :date: 2021-07-13

    .. change:: changed
        :tags: Documentation

        Update with latest images.

.. release:: 2.0.0-rc-1
    :date: 2021-06-18

    .. change:: changed
        :tags: UI

        Integrations are returned sorted by name in About page.

    .. change:: changed
        :tags: ConnectWidgetPlugin

        Improve error handling.

.. release:: 2.0.0-beta-4
    :date: 2021-06-07

    .. change:: new
        :tags: UI

        Allow connect to be always on top of other windows.

.. release:: 2.0.0-beta-3
    :date: 2021-05-21

    .. change:: changed
        :tags: API

        Review ConnectWidgetPlugin base classes.


.. release:: 2.0.0-beta-2
    :date: 2021-03-18

    .. change:: new
        :tags: Ui

        Provide ability to extend connect through ConnectWidgets plugins.


.. release:: 2.0.0-beta-1
    :date: 2021-03-11

    .. change:: changed
        :tags: Ui

        Move to `Pyside2 <https://pypi.org/project/PySide2/>`_.

    .. change:: changed
        :tags: API

        Remove `ftrack-python-legacy-api <https://bitbucket.org/ftrack/ftrack-python-legacy-api/src/master/>`_
        dependency and dependent code.

        .. warning::

            Hooks using ftrack.EVENT_HANDLERS won't be discovered anymore.

    .. change:: new
        :tags: Ui

        Replace `QtExt <https://bitbucket.org/ftrack/qtext>`_ with `Qt.py <https://github.com/mottosso/Qt.py>`_ module.

    .. change:: changed
        :tags: changed

        Move connector integration codebase to `separate repository <https://bitbucket.org/ftrack/ftrack-connector-legacy>`_

    .. change:: new
        :tags: Setup

        Use setuptool_scm to infer version.

    .. change:: fixed
        :tags: Application launcher

        Standalone installation does not correctly inject dependencies at application startup.

    .. change:: changed
        :tags: code

        Port code to python3.


.. warning::

    This is the last version supporting `ftrack-python-legacy-api <https://bitbucket.org/`


.. release:: 1.1.10
    :date: 2021-05-21

    .. change:: fixed
        :tags: doc

        Provide requirement file for RTD builds... release:: 1.1.9

    :date: 2021-03-11

    .. change:: fixed
        :tags: open_directory

        Opening component breaks on cloud paths.

    .. change:: fixed
        :tags: Application launcher

        Standalone installation does not correctly inject dependencies at application startup.


.. release:: 1.1.8
    :date: 2020-01-21

    .. change:: new
        :tags: Internal

        Added a lockfile mechanism so Connect will exit if another
        instance is already running. Users can pass a command-line
        flag, -a or --allow-multiple, to skip this check.

.. release:: 1.1.7
    :date: 2019-03-08

    .. change:: new
        :tags: Ui

        Added button in About dialog to create a Linux desktop entry file to
        make Connect appear in the applications menu.

.. release:: 1.1.6
    :date: 2018-10-8

    .. change:: changed
        :tags: Ui

        Update icons and style.

    .. change:: fixed
        :tags: Internal

        util.open_directory fails on Windows when path includes spaces.

.. release:: 1.1.5
    :date: 2018-9-13

     .. change:: fixed
        :tags: Logging

        logger breaks with non ascii path.

    .. change:: changed
        :tags: Logging

        Improve logging configuration.

    .. change:: fixed
        :tags: Ui

        Application versions are not correctly sorted.

.. release:: 1.1.4
    :date: 2018-04-27

    .. change:: fixed
        :tags: Import asset

        Import Asset breaks checking for asset in remote locations.

    .. change:: changed
        :tags: Crew

        Remove Crew widget chat and notifications.

    .. change:: changed
        :tags: Ui

        Added feature to hide the ftrack-connect UI on startup. This is done
        with the flag "--silent" or "-s".

.. release:: 1.1.3
    :date: 2018-02-02

    .. change:: fixed
       :tags: Plugins

        `ftrack.connect.plugin.debug-information` only published for the legacy
        api.

.. release:: 1.1.2
    :date: 2017-12-01

    .. change:: fixed
        :tags: Documentation

        Release notes page is not formatted correct.

.. release:: 1.1.1
    :date: 2017-11-16

    .. change:: fixed
        :tags: API

        Error when publishing in connect with non-task context.

.. release:: 1.1.0
    :date: 2017-09-12

    .. change:: changed
       :tags: Import asset

       Component location picker now defaults to location where the component
       exists. If a component exists in more than one location, the priority
       order determines the default location.

    .. change:: fixed
        :tags: Info dialog, Tasks dialog

        Info and Tasks dialogs are not compatible with recent versions of
        Qt.

    .. change:: fixed
        :tags: API

        All widgets are not compatible with recent versions of Qt.

.. release:: 1.0.1
    :date: 2017-07-11

    .. change:: fixed
        :tags: Asset manager

        Cannot change version of versions with a sequence component.

.. release:: 1.0.0
    :date: 2017-07-07

    .. change:: fixed
        :tags: API

        Errors in hooks are shown as event hub errors.

    .. change:: fixed
        :tags: Ui, Asset manager

        Asset manager fails to open in some rare cases.

    .. change:: fixed
        :tags: API

        Application search on disk does not follow symlinks.

    .. change:: changed
        :tags: Events, API

        The `ftrack.connect.application.launch` event is now also emitted through the new
        api. The event allows you to modify the command and/or environment of applications
        before they are launched.

    .. change:: changed
        :tags: API

        Changed Connector based plugins to use the new API to publish assets.

    .. change:: fixed
        :tags: Ui, Import asset

        Import asset dialog errors when a version has no user.

    .. change:: changed
        :tags: API

        Changed from using legacy API locations to using locations from the
        ftrack-python-api. Make sure to read the migration notes before
        upgrading:
        :ref:`release/migration/upcoming/developer_notes`

    .. change:: fixed
        :tags: Internal

        Fixed occasional X11 related crashes when launching actions on Linux.

    .. change:: changed
        :tags: Publish

        The new api and locations are used for publishing.

        .. seealso::

            :ref:`Read more <release/migration/upcoming/developer_notes>`

    .. change:: changed
        :tags: Internal

        X11 windows system is not thread safe.

    .. change:: changed
        :tags: Ui, Asset manager, Internal

        Update color on version indicator in asset manager.

    .. change:: fixed
        :tags: Settings

        Numberic settings cannot be set to higher than 99.

.. release:: 0.1.33
    :date: 2017-01-17

    .. change:: fixed
        :tags: Documentation

        Installation and usage instructions are confusing for users who have
        downloaded the pre-built package.

.. release:: 0.1.32
    :date: 2016-12-01

    .. change:: fixed
        :tags: API

        Switched to require ftrack-python-api > 1.0.0.

.. release:: 0.1.31
    :date: 2016-12-01

    .. change:: fixed
        :tags: Widget

        Entity picker may cause instability on some combinations of
        platforms and applications.

    .. change:: new
        :tags: Asset version scanner

        Added new method to scan for new asset versions.

.. release:: 0.1.30
    :date: 2016-09-23

    .. change:: fixed
        :tags: Asset manager

        Asset manager fails to switch versions if an asset is removed without
        refreshing the list.

.. release:: 0.1.29
    :date: 2016-09-21

    .. change:: fixed
        :tags: Internal

        Wrapper for PySide2 and Qt5 does not work properly on Windows.

.. release:: 0.1.28
    :date: 2016-09-16

    .. change:: changed
        :tags: Internal

        Add wrapper for PySide2 / Qt5 to support Maya 2017 and other future
        applications that rely on later versions of Qt.

    .. change:: fixed
        :tags: Internal, API

        Connect break in case of slow connection or missing url icon.

    .. change:: changed
        :tags: Internal

        Speedup asset manager.

    .. change:: fixed
        :tags: Internal

        Connect logs are saved to the wrong directory.

.. release:: 0.1.27
    :date: 2016-08-08

    .. change:: new
        :tags: Actions

        Added default action to reveal a Component in the OS default file
        browser.

.. release:: 0.1.26
    :date: 2016-07-19

    .. change:: new
        :tags: Internal

        Logs are now written to file and the logs directory can be accessed
        via the about menu.

.. release:: 0.1.25
    :date: 2016-06-07

    .. change:: changed
        :tags: Internal

        Improve support for debugging tools.

    .. change:: fixed
        :tags: Asset manager

        Asset versioning change breaks if versions has been deleted.

.. release:: 0.1.24
    :date: 2016-06-07

    .. change:: fixed
        :tags: Login

        Error when starting connect with invalid ftrack server URL.

.. release:: 0.1.23
    :date: 2016-05-06

    .. change:: fixed
        :tags: Events, API

        The `ftrack.connect.publish-components` event listener does not work
        correctly when using Windows.

.. release:: 0.1.22
    :date: 2016-05-02

    .. change:: new
        :tags: Events, API

        Added new `ftrack.connect.publish-components` event listener which
        can be used to publish components from applications not supporting
        the :term:`locations <ftrack:location>` framework.

    .. change:: changed
        :tags: Login

        Login details and credentials are now stored in a json file in the
        platform specific user data folder instead of using QSettings.

    .. change:: fixed
        :tags: Login

        Unable to logout on some platforms.

.. release:: 0.1.21
    :date: 2016-03-30

    .. change:: fixed
        :tags: Events, API

        Event listeners using new API may be registered twice.

.. release:: 0.1.20
    :date: 2016-03-14

    .. change:: new
        :tags: Plugins

        Added a menu option to open the default plugin directory.

    .. change:: changed
        :tags: Login

        Improved error handling for invalid server URLs.

    .. change:: new
        :tags: Login

        Added ability to login using regular users credentials via web interface
        instead of API key. Username and API key fields are therefore hidden by
        default in the ftrack connect login screen.

    .. change:: new
        :tags: Events

        ftrack connect will now respond to the ftrack.connect.discover event
        which can be used to identify if ftrack connect is running for the
        current user.

    .. change:: new
        :tags: Location

        Paths for custom locations that are implemented in the new Python
        API, :ref:`ftrack-python-api <ftrack-python-api:introduction>`,
        are now resolved in Connect.

    .. change:: new
        :tags: Location Scenario

        Added a new hook that can be used to detect problems and present
        information to the user.

        .. seealso::

            :ref:`Verify startup hook <developing/hooks/verify_startup>`

    .. change:: new
        :tags: Location Scenario

        Added a configure storage scenario widget that will be shown on startup
        if a storage scenario has not been configured on the server.

    .. change:: changed
        :tags: Event plugins

        Event plugins are now loaded for the new Python API,
        :ref:`ftrack-python-api <ftrack-python-api:introduction>`.
        :ref:`Read more <release/migration/0.1.20/developer_notes>`

    .. change:: fixed
        :tags: Ui

        Restore :py:class:`ftrack_connect.panelcom.PanelComInstance` communication with contextSelector,
        so changes to the environments get reflected into the widgets.

.. release:: 0.1.19
    :date: 2016-01-08

    .. change:: new
        :tags: Context Selector

        Added new
        :py:class:`ftrack_connect.ui.widget.context_selector.ContextSelector`
        widget that can be used to present and browse for a context.

    .. change:: changed

        Removed BrowseTasksSmallWidget in favor of
        :py:class:`ftrack_connect.ui.widget.context_selector.ContextSelector`.

.. release:: 0.1.18
    :date: 2015-11-10

    .. change:: new

        Added new
        :py:class:`ftrack_connect.ui.widget.html_combobox.HtmlComboBox` widget
        and :py:class:`ftrack_connect.ui.widget.html_delegate.HtmlDelegate`.

.. release:: 0.1.17
    :date: 2015-10-16

    .. change:: fixed
        :tags: Actions

        The option *launch with latest* is not respected when launching *Adobe*
        applications.

    .. change:: fixed
        :tags: Developer, Actions

        When launching actions via connect, not all action data are passed when
        firing the launch event.

.. release:: 0.1.16
    :date: 2015-10-02

    .. change:: new

        Display more detailed information about ftrack connect in About window.

        .. seealso::

            :ref:`Add custom information to About window <developing/hooks/plugin_information>`

.. release:: 0.1.15
    :date: 2015-09-22

    .. change:: changed
        :tags: Entity Browser

        Added support for new workflow object icons in entity browser.

    .. change:: fixed
        :tags: Crew

        Humanized notification dates are not always correct.

    .. change:: fixed
        :tags: Publisher

        Clean up after a failed publish fails if not permitted to delete
        version.

.. release:: 0.1.14
    :date: 2015-09-08

    .. change:: new
        :tags: Actions

        Added support for launching actions from Connect.

        .. seealso :: :ref:`using/actions`

    .. change:: new
        :tags: Crew

        Added crew widgets for chat and notifications.

    .. change:: changed
        :tags: Actions

        Applications may now include *description* and *variant*.

    .. change:: changed
        :tags: Developer

        ``thumbnail.Base`` will no longer default to ellipsis shape. Use
        ``thumbnail.EllipsisBase`` for round thumbnails.

.. release:: 0.1.13
    :date: 2015-08-31

    .. change:: changed
        :tags: Publisher

        Update entity browser to support updated naming convention.

.. release:: 0.1.12
    :date: 2015-08-24

    .. change:: new
        :tags: Publisher

        Support custom object types and icons in entity browser.

.. release:: 0.1.11
    :date: 2015-06-05

    .. change:: changed
        :tags: Publisher

        File browser now defaults to home directory.

    .. change:: fixed
        :tags: Publisher

        File browser crashes if file is removed or renamed.

    .. change:: fixed
        :tags: Publisher

        File browser not being refreshed if closed and reopened.

.. release:: 0.1.10
    :date: 2015-05-06

    .. change:: fixed
        :tags: Publisher

        Can not add files via drag and drop with non-ascii characters in the path.

.. release:: 0.1.9
    :date: 2015-03-18

    .. change:: new
        :tags: Developer

        Added base widgets and connectors to be used by application plugins.

.. release:: 0.1.8
    :date: 2015-03-02

    .. change:: fixed
        :tags: Publisher

        Publisher browser breaks when objects and files have non-ascii
        characters.

    .. change:: new
        :tags: Developer, Tutorial

        Added tutorial on how to add you own custom applications and how
        to modify the environment. :ref:`Read more <developing/tutorial/custom_applications>`

    .. change:: changed
        :tags: Publisher

        Added the possibility to specify if you like to version up an existing
        version or create a new version when publishing.
        :ref:`Read more <using/publishing/choose_or_create_asset>`

.. release:: 0.1.7
    :date: 2015-02-03

    .. change:: fixed
        :tags: Publisher

        Publisher is stuck in processing state if publish fails.

.. release:: 0.1.6
    :date: 2015-01-30

    .. change:: change
        :tags: Developer

        Moved logic for finding and starting applications supported by legacy
        plugins from the ftrack connect core to the legacy plugins repository.

    .. change:: fixed

        Unable to launch NukeX on Windows.

    .. change:: fixed

        Wrong Nuke version is launched on Windows if several are installed.

    .. change:: fixed

        Hiero and HieroPlayer are not discovered on Windows.

.. release:: 0.1.5
    :date: 2015-01-26

    .. change:: change

        Include *all* environment variables when launching applications.

.. release:: 0.1.4
    :date: 2015-01-23

    .. change:: new

        Added :ref:`About <faq/where_can_i_see_information_about_my_ftrack_connect>`
        option to menu to display eg. version, logged in user and ftrack server
        url.

    .. change:: change

        Use a managed :term:`location` when publishing from adobe extensions to
        prevent publishing temporary files.

.. release:: 0.1.3
    :date: 2015-01-14

    .. change:: change

        Update default :ref:`action_discover <developing/hooks/action_discover>` and
        :ref:`action_launch <developing/hooks/action_launch>` hooks to
        support new format in ftrack 3.0.3.
        :ref:`Read more <release/migration/0_1_3/developer_notes/updated_action_hooks>`

    .. change:: new

        Support launching applications with legacy ftrack plugins enabled.

    .. change:: fixed

        Fix import error causing Nuke to not launch correctly via Connect.

.. release:: 0.1.2
    :date: 2014-12-17

    .. change::

        Release to match version for package. No changes introduced.

.. release:: 0.1.1
    :date: 2014-12-02

    .. change:: new

        Support publishing independently of applications.

    .. change:: new

        Provide default actions for discovering and launching locally installed
        applications.
