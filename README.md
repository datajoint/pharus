# DJ-GUI-API Backend

Built on top of `Flask`, `datajoint`, and `pyjwt`.

Requirements:
- Docker
- Docker Compose

## Run Locally

- Copy `local-docker-compose.yaml` to `docker-compose.yaml`. This file is untracked so feel free to modify as necessary.
- Check the first comment which will provide best instruction on how to start the service.

NOTE: The docker-compose file creates a docker network call dj-gui-api which is meant to connect to front end to this back end via reverse proxy for developemnt. Final deployment will be using K8 or electron with some production server for flask

## Run Tests

- Create a `.env` as appropriate for your setup:
```shell
HOST_UID=1000 # Unix UID associated with non-root login
PY_VER=3.8    # Python version: 3.6|3.7|3.8
IMAGE=djtest  # Image type:     djbase|djtest|djlab|djlabhub
DISTRO=alpine # Distribution:   alpine|debian
```
- Navigate to `LNX-docker-compose.yaml` and check first comment which will provide best instruction on how to start the service. Yes, the command is a bit long...