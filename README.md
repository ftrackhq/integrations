This monorepo contains the source code for ftrack integrations, divided on apps (ex: Connect), libs (ex: framework libraries) and projects (ex: Integrations).

See full [documentation here](https://developer.ftrack.com).

# Developing

We use [Poetry](https://python-poetry.org/) to build and test independent packages in this repository, and to manage the dependencies between them.

## Obtaining the source code

```bash
git clone https://github.com/ftrackhq/integrations
```

or download the source ZIP from the [Integrations repository](https://github.com/ftrackhq/integrations) on Github.


## Preparations

Follow these steps to prepare your environment:

1. Install Poetry.
2. Create a Python >=3.7, <3.12 virtual environment. If you're using an Apple Silicon chip, follow the instructions in the [How to install compatible PySide2 on Silicon based Mac](#how-to-install-compatible-pyside2-on-silicon-based-mac) section.

### How to install compatible PySide2 on Silicon based Mac 

Follow these steps to install a compatible version of PySide2 Python >=3.7, <3.12 on a Silicon-based Mac:

1. Open a Rosetta terminal:
    - Duplicate the terminal application and check the "Open using Rosetta" checkbox inside the "Get Info" right-click menu.
2. Install brew for x86_64 architecture:
    - Run the following command:
        ```bash
        arch -x86_64 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"
        ```
    - Create an alias named `ibrew` to identify the Intel brew:
        ```bash
        alias ibrew="arch -x86_64 /usr/local/bin/brew"
        ```
3. Install the Python version with the Intel brew:
    - Run the following command:
        ```bash
        ibrew install python@3.7
        ```
4. Install `virtualenv`:
    - Run the following command:
        ```bash
        /usr/local/opt/python@3.7/bin/pip3 install virtualenv
        ```
5. Create a new virtual environment and activate it:
    - Run the following command to create the virtualenv:
        ```bash
        /usr/local/opt/python@3.7/bin/python3 -m virtualenv <path-to-where-you-want-it>
        ```
    - Run the following command:
        ```bash
        source  <path-to-where-you-want-it>/bin/activate
        ```

## Black

We run Black version 23.1.0 on the codebase to ensure consistent formatting. 

To be sure that code is properly formatted before committing code, enable the Git black pre commit hook by running this commands::

```bash
pip install pre-commit
pre-commit install
```

## Testing
We run PyTest ^7.4 on the codebase to ensure the consistency of our monorepo.
Please make sure you pip install PyTest if you want to run the unit tests.

- Got to the repository root and execute the following command to run all the monorepo available unit tests:
```bash
PyTest
```
- And This command to execute a specific tests: (Example using framework)
```bash
PyTest tests/framework/unit/
```

## Build and publish libraries
- Update version of the library
- Update the poetry.lock file
- Update the release notes date and provide a PR
- Create a tag for the library to be released
- Once tag is pushed the CI action will start and will publish to PyPi test
- Review PyPi Test publication
- Approve the deployment on the CI and will automatically release to Prod pypi
- **Note: Remember that libraries has dependencies to other libraries, follow this release order if you want to make sure to always use he latest version: utils - constants - framework-core - qt-style - qt - framework-qt**

## Publish to PyPi Test:
- Add pypi test as publishable repository: https://python-poetry.org/docs/repositories/#publishable-repositories
- Configure credentials using the token provided in 1Password PyPi-TEST-ftrack-utils : https://python-poetry.org/docs/repositories/#publishable-repositories (Make sure to point to the testpypi repo)
    - poetry config pypi-token.testpypi <your-token>
- Publish to test Pypi:
    - poetry publish -r testpypi --build

# Repo overview

## Apps

| Package                   | Path                         | Description                                                                                                   |
|---------------------------|------------------------------|---------------------------------------------------------------------------------------------------------------|
| [connect](./apps/connect) | app/connect                  | The desktop application that discovers and launches the DCC integrations and drives widget plugins.           |

## Installers

| Package                                             | Path                         | Description                   |
|-----------------------------------------------------|------------------------------|-------------------------------|
| [connect-installer](./installers/connect-installer) | installers/connect-installer | ftrack Connect app installer  |

## Libs

| Package                                 | Path                | Description                                                                                          |
|-----------------------------------------|---------------------|------------------------------------------------------------------------------------------------------|
| [constants](./libs/constants)           | libs/constants      | ftrack constants integrations library                                                                | 
| [framework-core](./libs/framework-core) | libs/framework-core | The core framework library                                                                           | 
| [framework-qt](./libs/framework-qt)     | libs/framework-qt   | Integrations Framework qt library, contains framework qt widgets and utilities used in the framework | 
| [qt](./libs/qt)                         | libs/qt             | ftrack qt integrations library, contains generic qt widgets used in integrations                     | 
| [qt-style](./libs/qt-style)             | libs/qt-style       | ftrack qt-style contains the ftrack style for the qt library.                                        | 
| [utils](./libs/utils)                   | libs/utils          | ftrack utility library                                                                               | 

## Projects

| Package                                                               | Path                              | Description                                                                               |
|-----------------------------------------------------------------------|-----------------------------------|-------------------------------------------------------------------------------------------|
| [connect-publisher-widget](./projects/connect-publisher-widget)       | projects/connect-publisher-widget | The standalone publisher widget in Connect                                                |
| [connect-timetracker-widget](./projects/connect-timetracker-widget)   | projects/connect-timetracker-widget | TimeTracker connect widget                                                                |
| [framework-common-extensions](./projects/framework-common-extensions) | projects/framework-common-extensions | Framework project which contains the default provided common extensions for the framework |
| [framework-maya](./projects/framework-maya)                           | projects/framework-maya           | Maya DCC framework integration                                                            |
| [framework-nuke](./projects/framework-nuke)                           | projects/framework-nuke           | Nuke DCC framework integration                                                            |
| [framework-photoshop](./projects/framework-photoshop)                 | projects/framework-photoshop      | Photoshop DCC framework integration                                                       |
| [framework-photoshop-js](./projects/framework-photoshop-js)           | projects/framework-photoshop-js   | Photoshop DCC framework integration JS code                                               |
| [nuke-studio](./projects/nuke-studio)                                 | projects/nuke-studio              | Nuke Studio integration                                                                   |
| [rv](./projects/rv)                                                   | projects/rv                       | RV player integration                                                                     |

## Resource

| Package                   | Path           | Description                       |
|---------------------------|----------------|-----------------------------------|
| [style](./resource/style) | resource/style | ftrack integrations style package |


## Tests

| Package                       | Path           | Description                              |
|-------------------------------|----------------|------------------------------------------|
| [framework](./test/framework) | test/framework | Framework unit and manual tests package. |


## Tools

| Package                                                                  | Path                                 | Description                                      |
|--------------------------------------------------------------------------|--------------------------------------|--------------------------------------------------|
| [cookiecutter-framework-project](./tools/cookiecutter-framework-project) | tools/cookiecutter-framework-project | Cookiecutter template for framework integrations |
| [build](./tools/build.py)                                                | tools/build.py                       | Build tool to create connect plugins             |
