# ftrack Connect Publisher widget release Notes

## v24.7.0rc1
2024-07-05

* [fix] Add entity in the assetOptions when in method setEntity. To prevent missing asset versions.
* [changed] Adding logs to better debug errors.


## v24.5.0
2024-05-03

* [changed] Replace Qt.py imports to PySide2 and PySide6 on widgets.

## v24.4.0
2024-04-02

* [changed] Upgrade ftrack-utils version.
* [fix] Make sure publisher sets the entity on start.
* [changed] Ported from ftrack-connect-publisher-widget repo and aligned with Connect 3
* [changed] Use poetry as build system.

## v0.1.1
2022-05-18

* [changed] Move launcher base class from connect to widget.

## v0.1.0
2022-04-14
* [changed] Localise publisher code in separate connect plugin widget.