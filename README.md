# Integrations

This monorepo contains the source code for the ftrack pipeline integration framework, divided into packages.

## Developing

We use [Pants](https://www.pantsbuild.org/) to build and test the packages in this repository, and to manage the dependencies between them.

Each package can be built on it its own with either Poetry or Setuptools (depending on the package), but Pants is required to build the entire repository.

### Obtaining the source code

```bash
git clone https://github.com/ftrackhq/integrations
```

or download the source ZIP from the [Integrations repository](https://github.com/ftrackhq/integrations) on Github


### Building

A Github CI/CF provide automated builds of the packages in this repository on PRs, merge to main and on tagging of releases.

To build the entire repository, run:

```bash
./pants package ::
```

The resulting source distribution (sdist) and wheel will be out to: `dist/`


To build a single package:

```bash
./pants package projects/framework-maya
```

### Building Connect plugin

Connect requires packages to be built and distributes as plugins. 

Example on how to build the Maya DCC Connect plugin:

```bash
./pants package projects/framework-maya
cd dist
tar -xzvf framework-maya-1.2.3.tar.gz
cd framework-maya-1.2.3
# Create and activate a Python 3.7 virtual environment

# For Poetry, first add <path to repo>/tools to your PATH
python build.py build_plugin

# Setuptools:
python setup.py build_plugin
```

### Testing

Currently we do not have any tests in the repository, but we will add them in the future.


## Package overview

### Connect

The desktop application that discovers and launches the DCC integrations and drives widget plugins.

#### App

| Package                | Path            | Description        |
|------------------------|-----------------|--------------------|
| [connect](app/connect) | app/connect     | ftrack Connect app |

#### Installer

Kept in separate repository for now: [ftrack-connect-package](https://github.com/ftrackhq/ftrack-connect-package)


#### Application launcher

| Package                                                                   | Path                                    | Description                                |
|---------------------------------------------------------------------------|-----------------------------------------|--------------------------------------------|
| [application-launcher](projects/application-launcher)                     | projects/application-launcher           | The application launcher logic             |
| [connect-action-launcher-widget](projects/connect-action-launcher-widget) | projects/connect-action-launcher-widget | The action launcher widget in Connect      |

#### Publisher

| Package                                                                   | Path                                    | Description                                |
|---------------------------------------------------------------------------|-----------------------------------------|--------------------------------------------|
| [connect-publisher-widget](projects/connect-publisher-widget)             | projects/connect-publisher-widget       | The standalone publisher widget in Connect |


### Framework

The framework package group contains the DCC integrations and is divided into libraries and DCC integration projects.

#### Libraries

| Package                               | Path                  | Description                |
|---------------------------------------|-----------------------|----------------------------|
| [framework-core](libs/framework-core) | libs/framework-core   | The core framework library |
| [framework-qt](libs/framework-qt)     | libs/framework-qt     | The QT framework library   |


#### DCC integrations

| Package                                         | Path                       | Description                   |
|-------------------------------------------------|----------------------------|-------------------------------|
| [framework-maya](projects/framework-maya)       | projects/framework-maya    | Maya DCC integration          |
| [framework-nuke](projects/framework-nuke)       | projects/framework-nuke    | Nuke DCC integration          |
| [framework-houdini](projects/framework-houdini) | projects/framework-houdini | Houdini DCC integration       |
| [framework-3dsmax](projects/framework-3dsmax)   | projects/framework-3dsmax  | 3d Studio Max DCC integration |
| [framework-unreal](projects/framework-unreal)   | projects/framework-maya    | Unreal Engine DCC integration |

