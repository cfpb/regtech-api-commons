# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/cfpb/regtech-api-commons/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|---------------------------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| src/regtech\_api\_commons/api/\_\_init\_\_.py       |        2 |        0 |        0 |        0 |    100% |           |
| src/regtech\_api\_commons/api/router\_wrapper.py    |       13 |        1 |        2 |        1 |     87% |        12 |
| src/regtech\_api\_commons/models/\_\_init\_\_.py    |        2 |        0 |        0 |        0 |    100% |           |
| src/regtech\_api\_commons/models/auth.py            |       21 |        0 |       10 |        0 |    100% |           |
| src/regtech\_api\_commons/oauth2/\_\_init\_\_.py    |        4 |        0 |        0 |        0 |    100% |           |
| src/regtech\_api\_commons/oauth2/config.py          |       29 |        0 |        2 |        0 |    100% |           |
| src/regtech\_api\_commons/oauth2/oauth2\_admin.py   |       61 |       15 |        8 |        3 |     74% |37-38, 41->44, 49-51, 58, 62-64, 69-70, 75-77, 84 |
| src/regtech\_api\_commons/oauth2/oauth2\_backend.py |       31 |        0 |        4 |        1 |     97% |    29->38 |
|                                           **TOTAL** |  **163** |   **16** |   **26** |    **5** | **89%** |           |

1 empty file skipped.


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/cfpb/regtech-api-commons/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/cfpb/regtech-api-commons/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/cfpb/regtech-api-commons/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/cfpb/regtech-api-commons/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fcfpb%2Fregtech-api-commons%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/cfpb/regtech-api-commons/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.