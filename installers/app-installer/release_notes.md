# ftrack app installer release Notes


## upcoming

* [changed] Include the machine architecture in the macOS DMG name (platform.machine()) so the Intel (x86_64) and Apple Silicon (arm64) builds produce distinct artifacts.
* [fix] Import dmgbuild lazily inside the macOS installer; the module level import crashed the installer on Windows and Linux.
* [added] Add collect all for riffle.
* [changed] Add full ftrack_api and ftrack_Action_handler modules on connect package.
* [changed] Make sure Windows executable is code signed.
* [changed] Initial release supporting Windows, Mac and Linux
