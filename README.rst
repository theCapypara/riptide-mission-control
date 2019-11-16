|Riptide|
=========

.. |Riptide| image:: https://riptide-docs.readthedocs.io/en/latest/_images/logo.png
    :alt: Riptide

.. class:: center

    ======================  ===================  ===================  ===================
    *Main packages:*        lib_                 proxy_               cli_
    *Container-Backends:*   engine_docker_
    *Database Drivers:*     db_mysql_
    *Related Projects:*     configcrunch_
    *More:*                 docs_                repo_                docker_images_
    \                       mission_control
    ======================  ===================  ===================  ===================

.. _lib:            https://github.com/Parakoopa/riptide-lib
.. _cli:            https://github.com/Parakoopa/riptide-cli
.. _proxy:          https://github.com/Parakoopa/riptide-proxy
.. _configcrunch:   https://github.com/Parakoopa/configcrunch
.. _engine_docker:  https://github.com/Parakoopa/riptide-engine-docker
.. _db_mysql:       https://github.com/Parakoopa/riptide-db-mysql
.. _docs:           https://github.com/Parakoopa/riptide-docs
.. _repo:           https://github.com/Parakoopa/riptide-repo
.. _docker_images:  https://github.com/Parakoopa/riptide-docker-images
.. _mission_control: https://github.com/Parakoopa/riptide-mission-control

|build| |docs|

.. |build| image:: https://jenkins.riptide.parakoopa.de/buildStatus/icon?job=riptide-mission-control%2Fmaster
    :target: https://jenkins.riptide.parakoopa.de/blue/organizations/jenkins/riptide-mission-control/activity
    :alt: Build Status

.. |docs| image:: https://readthedocs.org/projects/riptide-docs/badge/?version=latest
    :target: https://riptide-docs.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Riptide is a set of tools to manage development environments for web applications.
It's using container virtualization tools, such as `Docker <https://www.docker.com/>`_
to run all services needed for a project.

It's goal is to be easy to use by developers.
Riptide abstracts the virtualization in such a way that the environment behaves exactly
as if you were running it natively, without the need to install any other requirements
the project may have.

It can be installed via pip by installing ``riptide-mission-control``.

Mission control (GraphQL API server)
------------------------------------

This repository provides a GraphQL API server to interact with Riptide via API.

This repository is based on `IlyaRadinsky/tornadoql <https://github.com/IlyaRadinsky/tornadoql/>`_ @ ac59f12.

Documentation
-------------

The complete documentation for Riptide can be found at `Read the Docs <https://riptide-docs.readthedocs.io/en/latest/>`_.