<div
<p align="center">
  <em>👷‍♀️ <b>Under Construction</b> 👷</em>
  <img src="https://raw.githubusercontent.com/datajoint/pharus/master/under_contruction.png" alt="construction_fig"/>
</p>
</div>

> ⚠️ The Pharus project is still early in its life and the maintainers are currently actively developing with a priority of addressing first critical issues directly related to the deliveries of [Alpha](https://github.com/datajoint/pharus/milestone/1) and [Beta](https://github.com/datajoint/pharus/milestone/2) milestones. Please be advised that while working through our milestones, we may restructure/refactor the codebase without warning until we issue our [Official Release](https://github.com/datajoint/pharus/milestone/3) currently planned as `0.1.0` on `2021-03-31`.

# Pharus

A generic REST API server backend for DataJoint pipelines built on top of `flask`, `datajoint`, and `pyjwt`.

Usage and API documentation currently available within method docstrings. See Python's `help(...)` utility.

## Requirements for Preferred Setup

- [Docker](https://docs.docker.com/get-docker/  )
- [Docker Compose](https://docs.docker.com/compose/install/)

## Run Locally w/ Docker

- Copy a `*-docker-compose.yaml` file corresponding to your usage to `docker-compose.yaml`. This file is untracked so feel free to modify as necessary. Idea is to commit anything generic but system/setup dependent should go on 'your' version i.e. local UID/GID, etc.
- Check the first comment which will provide the best instruction on how to start the service; yes, it is a bit long. Note: Any of the keyword arguments prepended to the `docker-compose` command can be safely moved into a dedicated `.env` and read automatically if they are not evaluated i.e. `$(...)`. Below is a brief description of the non-evaluated environment variables:

```shell
PY_VER=3.8    # Python version: 3.6|3.7|3.8
IMAGE=djtest  # Image type:     djbase|djtest|djlab|djlabhub
DISTRO=alpine # Distribution:   alpine|debian
AS_SCRIPT=    # If 'TRUE', will not keep container alive but run tests and exit
```

> ⚠️ Deployment options currently being considered are [Docker Compose](https://docs.docker.com/compose/install/) and [Kubernetes](https://kubernetes.io/docs/tutorials/kubernetes-basics/).

## Run Locally w/ Python

- Set environment variables for port assignment (`PHARUS_PORT`, defaults to 5000) and API route prefix (`PHARUS_PREFIX` e.g. `/api`, defaults to empty string).
- For development, use CLI command `pharus`. This method supports hot-reloading so probably best coupled with `pip install -e ...`.
- For production, use `gunicorn --bind 0.0.0.0:${PHARUS_PORT} pharus.server:app`.

## Run Tests for Development w/ Pytest and Flake8

- Set `pharus` testing environment variables:
  ```shell
  PKG_DIR=/opt/conda/lib/python3.8/site-packages/pharus # path to pharus installation
  TEST_DB_SERVER=example.com:3306 # testing db server address
  TEST_DB_USER=root # testing db server user (needs DDL privilege)
  TEST_DB_PASS=unsecure # testing db server password
  ```
- For syntax tests, run `flake8 ${PKG_DIR} --count --select=E9,F63,F7,F82 --show-source --statistics`
- For pytest integration tests, run `pytest -sv --cov-report term-missing --cov=${PKG_DIR} /main/tests`
- For style tests, run `flake8 ${PKG_DIR} --count --max-complexity=20 --max-line-length=95 --statistics`

## Creating Sphinx Documentation from Scratch

Recommend the follow to be ran within the `pharus` container in `docs` Docker Compose environment.

- Run the following commands and complete the prompts as requested.
  ```bash
  mkdir docs
  cd docs
  sphinx-quickstart
  ```
- In `docs/conf.py` add to the beginning:
  ```python
  import os
  import sys
  sys.path.insert(0, os.path.abspath('..'))
  ```
- In `docs/conf.py:extensions` append `['sphinx.ext.autodoc', 'sphinxcontrib.httpdomain']`. See `requirements_docs.txt` and `docker-compose-docs.yaml` for details on documentation dependencies.
- Run the following to automatically generate the API docs:
  ```bash
  sphinx-apidoc -o . .. ../tests/* ../setup.py
  ```
- Add `modules` within the `toctree` directive in `index.rst`.
- Build the docs by running:
  ```bash
  make html
  ```

## References

- DataJoint LabBook (a companion frontend)
  - https://github.com/datajoint/datajoint-labbook
- Under construction image credits
  - https://www.pngfind.com/mpng/ooiim_under-construction-tape-png-under-construction-transparent-png/
- Python Tutorial for Flask, Swagger, and Automated docs
  - https://realpython.com/flask-connexion-rest-api/#reader-comments
