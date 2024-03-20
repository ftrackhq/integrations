# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/ftrackhq/integrations/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                          |    Stmts |     Miss |   Cover |   Missing |
|------------------------------------------------------------------------------ | -------: | -------: | ------: | --------: |
| libs/constants/source/ftrack\_constants/\_\_init\_\_.py                       |       12 |        2 |     83% |     19-20 |
| libs/constants/source/ftrack\_constants/framework/\_\_init\_\_.py             |        6 |        0 |    100% |           |
| libs/constants/source/ftrack\_constants/framework/asset/\_\_init\_\_.py       |       19 |        0 |    100% |           |
| libs/constants/source/ftrack\_constants/framework/client/\_\_init\_\_.py      |        1 |        0 |    100% |           |
| libs/constants/source/ftrack\_constants/framework/component/\_\_init\_\_.py   |        2 |        0 |    100% |           |
| libs/constants/source/ftrack\_constants/framework/event/\_\_init\_\_.py       |       23 |        0 |    100% |           |
| libs/constants/source/ftrack\_constants/framework/plugin/\_\_init\_\_.py      |       13 |        0 |    100% |           |
| libs/constants/source/ftrack\_constants/framework/tools/\_\_init\_\_.py       |        1 |        0 |    100% |           |
| libs/constants/source/ftrack\_constants/framework/tools/types/\_\_init\_\_.py |        6 |        0 |    100% |           |
| libs/constants/source/ftrack\_constants/qt/\_\_init\_\_.py                    |        1 |        0 |    100% |           |
| libs/constants/source/ftrack\_constants/qt/theme/\_\_init\_\_.py              |        4 |        0 |    100% |           |
| libs/constants/source/ftrack\_constants/status/\_\_init\_\_.py                |       10 |        0 |    100% |           |
| libs/framework-core/source/ftrack\_framework\_core/\_\_init\_\_.py            |        8 |        2 |     75% |     13-14 |
| libs/framework-core/source/ftrack\_framework\_core/configure\_logging.py      |       47 |        6 |     87% |31-35, 72-78 |
| libs/framework-core/source/ftrack\_framework\_core/engine/\_\_init\_\_.py     |      111 |       37 |     67% |29, 58, 76-77, 85, 123-161, 170, 185, 198, 234-251 |
| libs/framework-core/source/ftrack\_framework\_core/exceptions/\_\_init\_\_.py |        2 |        0 |    100% |           |
| libs/framework-core/source/ftrack\_framework\_core/exceptions/engine.py       |        3 |        1 |     67% |        11 |
| libs/framework-core/source/ftrack\_framework\_core/exceptions/plugin.py       |       21 |       12 |     43% |15, 25-27, 33-42, 51 |
| libs/framework-core/source/ftrack\_framework\_core/plugin/\_\_init\_\_.py     |       28 |        9 |     68% |14, 21, 46, 54, 61-74 |
| libs/framework-core/source/ftrack\_framework\_core/plugin/plugin\_info.py     |       24 |        2 |     92% |    10, 52 |
| libs/framework-core/source/ftrack\_framework\_core/registry/\_\_init\_\_.py   |      105 |       46 |     56% |19, 26, 33, 40, 47, 54, 61, 68, 72, 99-105, 113, 130, 134, 136, 138, 149-150, 169-170, 177-178, 190-192, 199-230 |
| libs/utils/source/ftrack\_utils/\_\_init\_\_.py                               |        6 |        2 |     67% |     13-14 |
| libs/utils/source/ftrack\_utils/decorators/\_\_init\_\_.py                    |        3 |        0 |    100% |           |
| libs/utils/source/ftrack\_utils/decorators/asynchronous.py                    |       18 |        4 |     78% |     25-28 |
| libs/utils/source/ftrack\_utils/decorators/session.py                         |       19 |       16 |     16% |      9-38 |
| libs/utils/source/ftrack\_utils/decorators/track\_usage.py                    |       49 |        5 |     90% |71, 89, 110-111, 129 |
| libs/utils/source/ftrack\_utils/directories/\_\_init\_\_.py                   |        0 |        0 |    100% |           |
| libs/utils/source/ftrack\_utils/directories/scan\_dir.py                      |        6 |        4 |     33% |     11-18 |
| libs/utils/source/ftrack\_utils/extensions/\_\_init\_\_.py                    |        0 |        0 |    100% |           |
| libs/utils/source/ftrack\_utils/extensions/registry.py                        |       71 |       55 |     23% |22-25, 38-65, 72-76, 81-139 |
| libs/utils/source/ftrack\_utils/modules/\_\_init\_\_.py                       |        0 |        0 |    100% |           |
| libs/utils/source/ftrack\_utils/modules/scan\_modules.py                      |       13 |        0 |    100% |           |
| libs/utils/source/ftrack\_utils/server/\_\_init\_\_.py                        |        2 |        0 |    100% |           |
| libs/utils/source/ftrack\_utils/server/send\_event.py                         |       16 |        2 |     88% |     34-35 |
| libs/utils/source/ftrack\_utils/server/track\_usage.py                        |        8 |        1 |     88% |        22 |
| libs/utils/source/ftrack\_utils/usage/\_\_init\_\_.py                         |        1 |        0 |    100% |           |
| libs/utils/source/ftrack\_utils/usage/track\_usage.py                         |       24 |        1 |     96% |        28 |
| libs/utils/source/ftrack\_utils/version/\_\_init\_\_.py                       |       31 |       22 |     29% |13-20, 24-31, 38-52 |
| tests/framework/unit/\_\_init\_\_.py                                          |        0 |        0 |    100% |           |
| tests/framework/unit/test\_engine.py                                          |       49 |        0 |    100% |           |
|                                                                     **TOTAL** |  **763** |  **229** | **70%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/ftrackhq/integrations/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/ftrackhq/integrations/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ftrackhq/integrations/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/ftrackhq/integrations/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fftrackhq%2Fintegrations%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/ftrackhq/integrations/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.