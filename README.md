
This monorepo contains the source code for the ftrack pipeline integration framework, divided into packages.

# Developing

We use [Pants](https://www.pantsbuild.org/) to build and test the packages in this repository, and to manage the dependencies between them.

Each package can be built on it its own with either Poetry or Setuptools (depending on the package), but Pants is required to build the entire repository.

## Obtaining the source code

```bash
git clone https://github.com/ftrackhq/integrations
```

or download the source ZIP from the [Integrations repository](https://github.com/ftrackhq/integrations) on Github


## Preparations

Follow these steps to prepare your environment:

1. Install Poetry.
2. Create a Python 3.7 virtual environment. If you're using an Apple Silicon chip, follow the instructions in the [How to install compatible PySide2 on Silicon based Mac](#how-to-install-compatible-pyside2-on-silicon-based-mac) section.

### How to install compatible PySide2 on Silicon based Mac 

Follow these steps to install a compatible version of PySide2 Python 3.7 on a Silicon-based Mac:

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

We run Black version 23 on the codebase to ensure consistent formatting. 

If updating or adding BUILD files, remember to have them properly formatted before committing otherwise CI will fail:

```bash
pants fmt --lint-only="black" ::
```

To check that BUILD files are properly formatted:

```bash
pants lint check --lint-only="black" ::
```

To be sure that code is properly formatted before committing code, enable the Git black pre commit hook by running this commands::

```bash
pip install pre-commit
pre-commit install
```


To format the code manually before committing, run:

```bash
black -l 79 --skip-string-normalization .
```


## Building

A GitHub CI/CF provide automated builds of the packages in this repository on PRs, merge to main and on tagging of releases.

To build the entire repository, run:

```bash
./pants package ::
```

The resulting source distribution (sdist) and wheel will be out to: `dist/`


To build a single package:

```bash
./pants package projects/framework-maya
```

## Building Connect plugin

Connect requires packages to be built and distributes as plugins. 

Example on how to build the Maya DCC Connect plugin:

```bash
./pants package projects/framework-maya
cd dist
tar -xzvf framework-maya-1.2.3.tar.gz
cd framework-maya-1.2.3
# Create and activate a Python 3.7 virtual environment
python setup.py build_plugin
```

## Testing

Currently we do not have any tests in the repository, but we will add them in the future.

## Publish to PyPi Test:
- Add pypi test as publishable repository: https://python-poetry.org/docs/repositories/#publishable-repositories
- Configure credentials using the token provided in 1Password PyPi-TEST-ftrack-utils : https://python-poetry.org/docs/repositories/#publishable-repositories (Make sure to point to the testpypi repo)
    - poetry config pypi-token.testpypi <your-token>
- Publish to test Pypi:
    - poetry publish -r testpypi --build

# Package overview

## Connect

The desktop application that discovers and launches the DCC integrations and drives widget plugins.

### App

| Package                                           | Path                         | Description                  |
|---------------------------------------------------|------------------------------|------------------------------|
| [connect](apps/connect)                           | app/connect                  | ftrack Connect app           |
| [connect-installer](installers/connect-installer) | installers/connect-installer | ftrack Connect app installer |


### Application launcher

| Package                                                                   | Path                                    | Description                                | RC                                                                              |
|---------------------------------------------------------------------------|-----------------------------------------|--------------------------------------------|---------------------------------------------------------------------------------|
| [application-launcher](projects/application-launcher)                     | projects/application-launcher           | The application launcher logic             | [application-launcher-rc](projects/application-launcher/rc)                     |
| [connect-action-launcher-widget](projects/connect-action-launcher-widget) | projects/connect-action-launcher-widget | The action launcher widget in Connect      | [connect-action-launcher-widget-rc](projects/connect-action-launcher-widget/rc) |


### Framework integrations

The framework package group contains the DCC integrations and is divided into libraries and DCC integration projects.

#### Libraries

| Package                               | Path                  | Description                | RC                                          |
|---------------------------------------|-----------------------|----------------------------|---------------------------------------------|
| [framework-core](libs/framework-core) | libs/framework-core   | The core framework library | [framework-core-rc](libs/framework-core/rc) |
| [framework-qt](libs/framework-qt)     | libs/framework-qt     | The QT framework library   | [framework-qt-rc](libs/framework-qt/rc)     |


#### DCC integrations

| Package                                         | Path                       | Description                   | RC                                                    |
|-------------------------------------------------|----------------------------|-------------------------------|-------------------------------------------------------|
| [framework-maya](projects/framework-maya)       | projects/framework-maya    | Maya DCC integration          | [framework-maya-rc](projects/framework-maya/rc)       |
| [framework-nuke](projects/framework-nuke)       | projects/framework-nuke    | Nuke DCC integration          | [framework-nuke-rc](projects/framework-nuke/rc)       |
| [framework-houdini](projects/framework-houdini) | projects/framework-houdini | Houdini DCC integration       | [framework-houdini-rc](projects/framework-houdini/rc) |
| [framework-3dsmax](projects/framework-3dsmax)   | projects/framework-3dsmax  | 3d Studio Max DCC integration | [framework-3dsmax-rc](projects/framework-3dsmax/rc)   |
| [framework-unreal](projects/framework-unreal)   | projects/framework-unreal  | Unreal Engine DCC integration | [framework-unreal-rc](projects/framework-unreal/rc)   |

### Standalone integrations

| Package                             | Path                 | Description             | RC                                        |
|-------------------------------------|----------------------|-------------------------|-------------------------------------------|
| [rv](projects/rv)                   | projects/rv          | RV player integration   | [rv-rc](projects/rv/rc)                   |
| [nuke-studio](projects/nuke-studio) | projects/nuke-studio | Nuke Studio integration | [nuke-studio-rc](projects/nuke-studio/rc) |


### Connect publisher

| Package                                                                   | Path                                    | Description                                |
|---------------------------------------------------------------------------|-----------------------------------------|--------------------------------------------|
| [connect-publisher-widget](projects/connect-publisher-widget)             | projects/connect-publisher-widget       | The standalone publisher widget in Connect |


### Tools

| Package                                                | Path                           | Description                                                |
|--------------------------------------------------------|--------------------------------|------------------------------------------------------------|
| [connect-cookiecutter](tools/connect-cookiecutter)     | tools/connect-cookiecutter     | Cookiecutter template for Connect plugins                  |
| [framework-cookiecutter](tools/framework-cookiecutter) | tools/framework-cookiecutter   | Cookiecutter template for Framework (integrations) plugins |
