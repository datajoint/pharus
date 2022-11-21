User Documentation
==================

``pharus`` is a generic REST API server backend for `DataJoint <https://datajoint.io>`_ pipelines built on top of ``flask``, ``datajoint``, and ``pyjwt``.

- `Documentation <https://datajoint.github.io/pharus>`_
- `PyPi Package <https://pypi.org/project/pharus/>`_
- `Docker Image <https://hub.docker.com/r/datajoint/pharus>`_
- `Release <https://github.com/datajoint/pharus/releases/latest>`_
- `Source <https://github.com/datajoint/pharus>`_

Installation
------------

If you have not done so already, please install the following dependencies.

- `Docker <https://docs.docker.com/get-docker/>`_
- `Docker Compose <https://docs.docker.com/compose/install/>`_

Prerequisites
-------------

Download the ``docker-compose-deploy.yaml`` docker environment from the source located `here <https://github.com/datajoint/pharus/releases/latest/download/docker-compose-deploy.yaml>`_.

Running the API server
----------------------

To start the API server, use the command:

    .. code-block:: bash

        PHARUS_VERSION=0.6.3 docker-compose -f docker-compose-deploy.yaml up -d

To stop the API server, use the command:

    .. code-block:: bash

        PHARUS_VERSION=0.6.3 docker-compose -f docker-compose-deploy.yaml down

References
----------

- DataJoint

  - https://datajoint.io

- DataJoint LabBook (a companion frontend)
  
  - https://github.com/datajoint/datajoint-labbook
