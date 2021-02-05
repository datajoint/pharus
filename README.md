<p align="center">
 <img src="under_contruction.png" alt="train_perf_fig" height="640" width="960"/>
    <br>
    <em>Figure 1 training process of NN.</em>
</p>
<!-- <figcaption style="text-align:center; font-size: 50px"><p>👷‍♀️ <b>Under Construction</b> 👷</p></figcaption>
<img src="./under_contruction.png" align="middle"/> -->


# DJ-GUI-API Backend

Built on top of `flask`, `datajoint`, and `pyjwt`.

Requirements:
- Docker
- Docker Compose

## Run Locally

- Copy `local-docker-compose.yaml` to `docker-compose.yaml`. This file is untracked so feel free to modify as necessary.
- Check the first comment which will provide best instruction on how to start the service.

NOTE: The docker-compose file creates a docker network called `dj-gui-api` which is meant to connect the front end to the back end via reverse proxy for development. Final deployment will be using K8S or electron with some production server for flask.

## Run Tests

- Create a `.env` as appropriate for your setup:
```shell
HOST_UID=1000 # Unix UID associated with non-root login
PY_VER=3.8    # Python version: 3.6|3.7|3.8
IMAGE=djtest  # Image type:     djbase|djtest|djlab|djlabhub
DISTRO=alpine # Distribution:   alpine|debian
```
- Navigate to `LNX-docker-compose.yaml` and check first comment which will provide best instruction on how to start the service. Yes, the command is a bit long...

## References

- Under construction image credits:
  - https://www.pngfind.com/mpng/ooiim_under-construction-tape-png-under-construction-transparent-png/