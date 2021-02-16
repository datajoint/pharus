<div
<p align="center">
  <em>👷‍♀️ <b>Under Construction</b> 👷</em>
  <img src="under_contruction.png" alt="construction_fig"/>  
</p>
</div>

> :warning: The Pharus project is still early in its life and the maintainers are currently actively developing with a priority of addressing first critical issues directly related to the deliveries of [Alpha](https://github.com/datajoint/pharus/milestone/1) and [Beta](https://github.com/datajoint/pharus/milestone/2) milestones. Please be advised that while working through our milestones, we may restructure/refactor the codebase without warning until we issue our [Official Release](https://github.com/datajoint/pharus/milestone/3) currently planned as `0.1.0` on `2021-03-31`.

# Pharus

A generic REST API server backend for DataJoint pipelines built on top of `flask`, `datajoint`, and `pyjwt`.

Requirements:
- [Docker](https://docs.docker.com/get-docker/  )
- [Docker Compose](https://docs.docker.com/compose/install/)

## Run Locally

- Copy a `*-docker-compose.yaml` file corresponding to your usage to `docker-compose.yaml`. This file is untracked so feel free to modify as necessary.
- Check the first comment which will provide best instruction on how to start the service.

> :warning: Deployment options currently being considered are [Docker Compose](https://docs.docker.com/compose/install/) and [Kubernetes](https://kubernetes.io/docs/tutorials/kubernetes-basics/).

## Run Tests for Development

- Create a `.env` as appropriate for your setup:
```shell
PY_VER=3.8    # Python version: 3.6|3.7|3.8
IMAGE=djtest  # Image type:     djbase|djtest|djlab|djlabhub
DISTRO=alpine # Distribution:   alpine|debian
AS_SCRIPT=    # If 'TRUE', will not keep container alive but run tests and exit
```
- Navigate to `test-docker-compose.yaml` and check first comment which will provide best instruction on how to start the service. Yes, the command is a bit long...

## References

- DataJoint LabBook (a companion frontend)
  - https://github.com/datajoint/datajoint-labbook
- Under construction image credits
  - https://www.pngfind.com/mpng/ooiim_under-construction-tape-png-under-construction-transparent-png/
