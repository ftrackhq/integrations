# ftrack Connect installer release Notes

## v24.3.0rc2
2024-03-26

* [changed] Release connect 3.0.0rc2

## v24.3.0rc1
2024-03-25

* [changed] Removed docker files.
* [new] Windows codesign support.
* [new] Rocky linux 8 and 9 support added and removed Centos7 support. (Centos8 still working with Rocky8 build)
* [changed] MacOS codesign process updated, replaced the deprecated alttool for the new notarytool.
* [changed] Package name renamed from ftrack-Connect-... to ftrack_connect-...
* [changed] Augmented installer to cope with new Connect 3 module format.

## v2.1.1
2023-04-27

* [fixed] Release connect 2.1.1

## v2.1.0
2023-04-05

* [None] Release connect 2.1.0

## v2.0.1
2022-09-01

* [changed] Release connect 2.0.1.

## v2.0.0
2022-07-07

* [fixed] logo.svg used in linux shortcut does not exist.

## v2.0.0-rc-6
2022-06-07

* [changed] Remove plugin manager from package.

## v2.0.0-rc-5
2022-03-25

* [changed] Bump ftrack-connect-plugin-manager to 0.1.3.
* [changed] Installation path does not include Connect version.
* [changed] Update icon set based on new style.

## v2.0.0-rc-4
2022-01-15

* [added] ftrack-connect-plugin-manager is now included in package.
* [fixed] DMG can now be build without needing to code sign it.
* [fixed] Connect package does not provide a consistent ProductCode when generating msi installer.
* [fixed] Cinesync action error if context is not provided.

## v1.1.2
2020-01-28

* [changed] ftrack api 1.8.2
* [changed] ftrack connect nuke studio 2.2.4
* [changed] ftrack connect maya 1.2.3
* [changed] ftrack connect nuke 1.2.2
* [changed] ftrack connect hieroplayer 1.3.1
* [changed] ftrack connect rv 4.0
* [changed] ftrack connect foundry 1.2.1
* [changed] ftrack connect maya publish 0.6.3
* [changed] ftrack connect nuke publish 0.6.3
* [changed] ftrack connect pipeline 0.8.4
* [changed] ftrack action handler 0.1.4
* [changed] ftrack connect 1.1.8
* [added] ftrack connect houdini 0.2.3

::::note
    These inbetween release notes are outdated and not available at this point.
::::

## v0.1.1
2014-12-01

* [new] Initial version

