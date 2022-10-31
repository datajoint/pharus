# DataJoint Pharus User Documentation 

## Installation

### Dependencies

DataJoint Pharus requires `Docker` and `Docker Compose` which can be downloaded at:

+ [Docker](https://docs.docker.com/get-docker/)
+ [Docker Compose](https://docs.docker.com/compose/install/)

### Prerequisites

Download the docker environment needed to run the API server
[here](https://github.com/datajoint/pharus/releases/latest/download/docker-compose-deploy.yaml).

### Running the API server

To start the API server, use the command:

```console
PHARUS_VERSION=0.5.6 docker-compose -f docker-compose-deploy.yaml up -d
```

To stop the API server, use the command:

```console
PHARUS_VERSION=0.5.6 docker-compose -f docker-compose-deploy.yaml down
```