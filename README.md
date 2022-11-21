# ftrack cookiecutter connect plugin

Cookiecutter template for a ftrack Connect plugin.

## Usage

First make sure you have cookiecutter installed on your python environment:

    pip install cookiecutter

### Generate new plugin:

     cookiecutter -f -o <path-to-your-ropo-folder> <path-to-coockiecutter-template-git-or-local-path> 
Example:

    cookiecutter -f -o /Users/ftrack/repos https://github.com/ftrackhq/ftrack-cookiecutter-connect-framework-plugin.git

* Fill up all the new plugin name input field when asked (All the other fields are automatically fill out by default).

Once the project is create you should initialise a local git repo with:

    git init

### Extend definitions repository with the new plugin definitions:

Clone definitions repository to your repository folder:

    cd <path-to-your-ropo-folder>
    git clone https://github.com/ftrackhq/ftrack-connect-pipeline-definition.git

Apply new plugin template to definitions repository:

    cookiecutter -f -c definition -o <path-to-your-ropo-folder> <path-to-coockiecutter-template-git-or-local-path>
Example:

    cookiecutter -f -c definition -o /Users/ftrack/repos https://github.com/ftrackhq/ftrack-cookiecutter-connect-framework-plugin.git

* Fill up all the new plugin name input field when asked (All the other fields are automatically fill out by default).

#### Note: Check the output - you may need to fix documentation underlining, add dependencies etc.

## Copyright and license

Copyright (c) 2022 ftrack

Licensed under the Apache License, Version 2.0 (the \"License\"); you
may not use this work except in compliance with the License. You may
obtain a copy of the License in the LICENSE.txt file, or at:

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an \"AS IS\" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.