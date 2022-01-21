General Notes
=============

Requirements for Preferred Setup
--------------------------------

- `Docker <https://docs.docker.com/get-docker/>`_
- `Docker Compose <https://docs.docker.com/compose/install/>`_

Run Locally w/ Docker
---------------------

- Copy the docker environment (i.e. ``*-docker-compose.yaml``) of your choice corresponding to your usage to ``docker-compose.yaml``. This file is untracked so feel free to modify as necessary. Idea is to commit anything generic but system/setup dependent should go on 'your' version i.e. local UID/GID, etc.
- Check the first header comment which will provide the best instruction on how to start the service; yes, it is a bit long. Note: Any of the keyword arguments prepended to the ``docker-compose`` command can be safely moved into a dedicated ``.env`` and read automatically if they are not evaluated i.e. ``$(...)``. Below is a brief description of the non-evaluated environment variables:

    .. code-block:: bash

        PY_VER=3.8    # Python version: 3.6|3.7|3.8
        IMAGE=djtest  # Image type:     djbase|djtest|djlab|djlabhub
        DISTRO=alpine # Distribution:   alpine|debian
        AS_SCRIPT=    # If 'TRUE', will not keep container alive but run tests and exit

.. note::

    Deployment options currently being considered are `Docker Compose <https://docs.docker.com/compose/install/>`_ and `Kubernetes <https://kubernetes.io/docs/tutorials/kubernetes-basics/>`_.

Run Locally w/ Python
---------------------

- Set environment variables for port assignment (``PHARUS_PORT``, defaults to 5000) and API route prefix (``PHARUS_PREFIX`` e.g. ``/api``, defaults to empty string).
- For development, use CLI command ``pharus``. This method supports hot-reloading so probably best coupled with ``pip install -e ...``.
- For production, use ``gunicorn --bind 0.0.0.0:${PHARUS_PORT} pharus.server:app``.

Run Tests for Development w/ Pytest, Flake8, Black
--------------------------------------------------

- Set ``pharus`` testing environment variables:

    .. code-block:: bash

        PKG_DIR=/opt/conda/lib/python3.8/site-packages/pharus # path to pharus installation
        TEST_DB_SERVER=example.com:3306 # testing db server address
        TEST_DB_USER=root # testing db server user (needs DDL privilege)
        TEST_DB_PASS=unsecure # testing db server password

- For syntax tests, run ``flake8 ${PKG_DIR} --count --select=E9,F63,F7,F82 --show-source --statistics``
- For pytest integration tests, run ``pytest -sv --cov-report term-missing --cov=${PKG_DIR} /main/tests``
- For style tests, run ``black $${PKG_DIR} --check -v --extend-exclude "^.*dynamic_api.py$"``

Creating Sphinx Documentation from Scratch
------------------------------------------

Recommend the follow to be ran within the ``pharus`` container in ``docs`` Docker Compose environment.

- Run the following commands and complete the prompts as requested.

    .. code-block:: bash

        mkdir docs
        cd docs
        sphinx-quickstart

- In ``docs/conf.py`` add to the beginning:

    .. code-block:: python

        import os
        import sys
        sys.path.insert(0, os.path.abspath('..'))

- In ``docs/conf.py:extensions`` append ``['sphinx.ext.autodoc', 'sphinxcontrib.httpdomain']``. See ``requirements_docs.txt`` and ``docker-compose-docs.yaml`` for details on documentation dependencies.
- Run the following to automatically generate the API docs:

    .. code-block:: bash

        sphinx-apidoc -o . .. ../tests/* ../setup.py

- Add ``modules`` within the ``toctree`` directive in ``index.rst``.
- Build the docs by running:

    .. code-block:: bash

        make html

References
----------

- DataJoint

  - https://datajoint.io

- DataJoint LabBook (a companion frontend)

  - https://github.com/datajoint/datajoint-labbook

- Python Tutorial for Flask, Swagger, and Automated docs

  - https://realpython.com/flask-connexion-rest-api/#reader-comments
