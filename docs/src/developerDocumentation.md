# DataJoint Pharus Developer Documentation

## Requirements for Preferred Setup

+ [Docker](https://docs.docker.com/get-docker/)
+ [Docker Compose](https://docs.docker.com/compose/install/)

## Run Locally with Docker

+ Copy the docker environment (`*-docker-compose.yaml`) corresponding to your
usage to `docker-compose.yaml`. This file is untracked and can be modified as
necessary. Generic commits can be made to the `docker-compose.yaml` file but
local settings including system- and setup-dependent
settings should be kept on your local docker-compose. 

+ The first header comment provides instructions on how to start the service.
  Note: Any keyword arguments prepended to the `docker-compose` command can be
  safely moved into a dedicated `.env` and read automatically if they are not
  evaluated, i.e. `$(...)`. Below is a description of the non-evaluated
  environment variables:
  
```console
  PY_VER=3.8    # Python version: 3.6|3.7|3.8
  IMAGE=djtest  # Image type:     djbase|djtest|djlab|djlabhub
  DISTRO=alpine # Distribution:   alpine|debian
  AS_SCRIPT=    # If 'TRUE', will not keep container alive but run tests and exit
```

+ Deployment options currently being considered are [Docker Compose](https://docs.docker.com/compose/install/) and
  [Kubernetes](https://kubernetes.io/docs/tutorials/kubernetes-basics/).

## Run Locally with Python

+ Set environment variables for port assignment (`PHARUS_PORT`, defaults to
  5000) and API route prefix (`PHARUS_PREFIX`: e.g. `/api`, defaults to empty
        string). 

+ For development, use CLI command `pharus`. This method supports hot-reloading
  so it should be coupled with `pip install -e ...`. 

+ For production, use `gunicorn --bind 0.0.0.0:${PHARUS_PORT}
  pharus.server:app`.

## Run Tests for Development

+ Running tests requires `Pytest`, `Flake8`, and `Black`.

+ Set `pharus` testing environment variables:

```console
PKG_DIR=/opt/conda/lib/python3.8/site-packages/pharus # path to pharus installation
TEST_DB_SERVER=example.com:3306 # testing db server address
TEST_DB_USER=root # testing db server user (needs DDL privilege)
TEST_DB_PASS=unsecure # testing db server password
```

+ For syntax tests, run `flake8 ${PKG_DIR} --count --select=E9,F63,F7,F82
  --show-source --statistics`. 

+ For pytest integration tests, run `pytest -sv --cov-report term-missing
  --cov=${PKG_DIR} /main/tests`. 

+ For style tests, run: 

```console
black ${PKG_DIR} --check -v --extend-exclude "^.*dynamic_api.py$"
flake8 ${PKG_DIR} --count --max-complexity=20 --max-line-length=94 --statistics --exclude=*dynamic_api.py --ignore=W503
```
