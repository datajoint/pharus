# General Notes

## Requirements for Preferred Setup

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Run Locally w/ Docker

- Copy the docker environment (i.e. `docker-compose-*.yaml`) of your
  choice corresponding to your usage to `docker-compose.yaml`. This
  file is untracked so feel free to modify as necessary. Idea is to
  commit anything generic but system/setup dependent should go on
  your version i.e. local UID/GID, etc.

- Check the first header comment which will provide the best
  instruction on how to start the service.

  - Any of the keyword arguments prepended to the `docker compose`
    command can be safely moved into a dedicated `.env` and read
    automatically if they are not evaluated i.e. `$(...)`. Below is a
    brief description of the non-evaluated environment variables:

  ```console
  PY_VER=3.8    # Python version: 3.6|3.7|3.8
  IMAGE=djtest  # Image type:     djbase|djtest|djlab|djlabhub
  DISTRO=alpine # Distribution:   alpine|debian
  AS_SCRIPT=    # If 'TRUE', will not keep container alive but run tests and exit
  ```

!!! note
    Deployment options currently being considered are [Docker
    Compose](https://docs.docker.com/compose/install/) and
    [Kubernetes](https://kubernetes.io/docs/tutorials/kubernetes-basics/).

## Run Locally w/ Python

- Set environment variables for port assignment (`PHARUS_PORT`,
  defaults to 5000) and API route prefix (`PHARUS_PREFIX` e.g. `/api`,
  defaults to empty string).
- For development, use CLI command `pharus`. This method supports
  hot-reloading so probably best coupled with `pip install -e ...`.
- For production, use
  `gunicorn --bind 0.0.0.0:${PHARUS_PORT} pharus.server:app`.

## Run Tests for Development w/ Pytest, Flake8, Black

- Set `pharus` testing environment variables:

  ```console
  PKG_DIR=/opt/conda/lib/python3.8/site-packages/pharus # path to pharus installation
  TEST_DB_SERVER=example.com:3306 # testing db server address
  TEST_DB_USER=root # testing db server user (needs DDL privilege)
  TEST_DB_PASS=unsecure # testing db server password
  ```

- For syntax tests, run
  `flake8 ${PKG_DIR} --count --select=E9,F63,F7,F82 --show-source --statistics`

- For pytest integration tests, run
  `pytest -sv --cov-report term-missing --cov=${PKG_DIR} /main/tests`

- For style tests, run:

  ```console
  black ${PKG_DIR} --check -v --extend-exclude "^.*dynamic_api.py$"
  flake8 ${PKG_DIR} --count --max-complexity=20 --max-line-length=94 --statistics --exclude=*dynamic_api.py --ignore=W503
  ```

## Extending Pharus Routes

Pharus' routes can be extended through the spec sheet.

### Guide

1. Define the YAML spec sheet. Under `SciViz.component_interface.override`, in a string block:

   1. Import the `type_map` and base components from the pharus `component.interface` module, as well as any other libraries needed.
   2. Define a class that extends one of the base components. If extending `Component`, the rest verb must be manually set.

      - Within the class, define a `dj_query_route` method with the functionality of your custom route. Ensure it returns a dictionary.

   3. Extend the `type_map` with a mapping of the name of you want to give to the component to the new class.

      - The new name can now be used as a type in the `components` section of the spec.

2. Inject the spec into pharus
   1. Mount the spec sheet into the container.
   2. Set the `PHARUS_SPEC_PATH` environment variable.

### Example

```yaml
SciViz:
  auth:
    mode: database | oidc | none
  component_interface:
    override: |
      # import `type_map`, the base components to be extended, and any other libraries necessary
      from pharus.component_interface import type_map, Component

      # define custom class extending a base component
      class ExampleComponent(Component):
          # set necessary REST verb(s) if extending generic `Component`
          rest_verb=["POST"]

          # define `dj_query_route` method that returns some dictionary
          def dj_query_route(self):
              # some code
              return {"example": "example response"}

      # extend the `type_map` with a custom type mapped to the custom component
      type_map = {
          **type_map, 'ExampleType': ExampleComponent
      }
  pages:
    page:
      route: /page
      hidden: true
      grids:
        grid:
          type: fixed
          components:
            example_component:
              route: /example_route
              type: ExampleType
```

For more information about the spec sheet, visit the [SciViz docs](https://datajoint.com/docs/core/sci-viz/2.3/concepts/spec_sheet/).

## Creating MkDocs Documentation

Run the following command with the appropriate parameters:

```console
MODE="LIVE|QA|PUSH" PACKAGE=pharus UPSTREAM_REPO=https://github.com/datajoint/pharus.git HOST_UID=$(id -u) docker compose -f docs/docker-compose.yaml up --build
```

```console
MODE=LIVE       # `LIVE` for development, `QA` for testing, `PUSH` for production
PACKAGE=pharus  # The name of the folder containing the package files: `pharus` if not renamed
UPSTREAM_REPO=  # The URL of the upstream repository
```

## References

- DataJoint
  - <https://datajoint.io>
- DataJoint LabBook (a companion frontend)
  - <https://github.com/datajoint/datajoint-labbook>
- Python Tutorial for Flask, Swagger, and Automated docs
  - <https://realpython.com/flask-connexion-rest-api/#reader-comments>
