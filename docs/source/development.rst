.. _development:

Development
===========

To install for development:

1. Fork the `biweeklybudget <https://github.com/jantman/biweeklybudget>`_ repository on GitHub
2. Create a new branch off of master in your fork.

.. code-block:: bash

    $ virtualenv biweeklybudget
    $ cd biweeklybudget && source bin/activate
    $ pip install -e git+git@github.com:YOURNAME/biweeklybudget.git@BRANCHNAME#egg=biweeklybudget
    $ cd src/biweeklybudget

The git clone you're now in will probably be checked out to a specific commit,
so you may want to ``git checkout BRANCHNAME``.

Guidelines
----------

* pep8 compliant with some exceptions (see pytest.ini)
* 100% test coverage with pytest (with valid tests)

.. _development.docker_database:

Docker Database Container
-------------------------

To run a Dockerized database for your test environment:

.. code-block:: bash

    $ docker run -d --name budgettest -p 13306:3306 --env MYSQL_ROOT_PASSWORD=dbroot --env MYSQL_ROOT_HOST='%' mariadb:10.4.7
    # wait for the DB to start up
    $ docker exec -it budgettest sh -c 'exec mysql -uroot -pdbroot -e "CREATE DATABASE budgettest; CREATE DATABASE budgettest27; CREATE DATABASE budgettest36; CREATE DATABASE alembicLeft; CREATE DATABASE alembicRight;"'
    $ export DB_CONNSTRING='mysql+pymysql://root:dbroot@127.0.0.1:13306/budgettest?charset=utf8mb4'; export MYSQL_HOST=127.0.0.1; export MYSQL_PORT=13306; export MYSQL_USER=root; export MYSQL_PASS=dbroot; export MYSQL_DBNAME_LEFT=alembicLeft; export MYSQL_DBNAME_RIGHT=alembicRight
    # run your tests
    $ docker stop budgettest && docker rm budgettest

.. _development.loading_data:

Loading Data
------------

The sample data used for acceptance tests is defined in ``biweeklybudget/tests/fixtures/sampledata.py``.
This data can be loaded by `setting up the environment <_getting_started.setup>`
and then using the ``loaddata`` entrypoint (the following values for
options are actually the defaults, but are shown for clarity):

.. code-block:: bash

    loaddata -m biweeklybudget.tests.fixtures.sampledata -c SampleDataLoader

This entrypoint will **drop all tables and data** and then load fresh data from
the specified class.

If you wish, you can copy ``biweeklybudget/tests/fixtures/sampledata.py`` to your
`customization package <_getting_started.customization>` and edit it to load your own
custom data. This should only be required if you plan on dropping and reinitializing the
database often.

Testing
-------

Testing is done via `pytest <https://docs.pytest.org/en/latest/>`_, driven by `tox <https://tox.readthedocs.io/>`_.

* testing is as simple as:

  * ``pip install tox``
  * ``tox``

* If you want to pass additional arguments to pytest, add them to the tox command line after "--". i.e., for verbose pytext output on py27 tests: ``tox -e py27 -- -v``

For rapid iteration on tests, you can either use my
`toxit <https://github.com/jantman/misc-scripts/blob/master/toxit.py>`_ script
to re-run the test commands in an existing tox environment, or you can use
the ``bin/t`` and ``bin/ta`` scripts to run unit or acceptance tests,
respectively, on only one module.

Unit Tests
++++++++++

There are minimal unit tests, really only some examples and room to test some potentially fragile code. Run them via the ``^py\d+`` tox environments.

Integration Tests
+++++++++++++++++

There's a pytest marker for integration tests, effectively defined as anything that might use either a mocked/in-memory DB or the flask test client, but no HTTP server and no real RDBMS. Run them via the ``integration`` tox environment. But there aren't any of them yet.

Acceptance Tests
++++++++++++++++

There are acceptance tests, which use a real MySQL DB (see the connection string in ``tox.ini`` and ``conftest.py``) and a real Flask HTTP server, and selenium. Run them via the ``acceptance`` tox environment. Note that they're currently configured to use Headless Chrome; running them locally will require a modern Chrome version that supports the ``--headless`` flag (Chrome 59+) and a matching version of `chromedriver <https://sites.google.com/a/chromium.org/chromedriver/>`_.

The acceptance tests connect to a local MySQL database using a connection string specified by the ``DB_CONNSTRING`` environment variable, or defaulting to a DB name and user/password that can be seen in ``conftest.py``. Once connected, the tests will drop all tables in the test DB, re-create all models/tables, and then load sample data. After the DB is initialized, tests will run the local Flask app on a random port, and run Selenium backed by headless Chrome.

If you want to run the acceptance tests without dumping and refreshing the test database, export the ``NO_REFRESH_DB`` environment variable. Setting the ``NO_CLASS_REFRESH_DB``
environment variable will prevent refreshing the DB after classes that manipulate data; this will cause subsequent tests to fail but can be useful for debugging.

Running Acceptance Tests Against Docker
+++++++++++++++++++++++++++++++++++++++

The acceptance tests have a "hidden" hook to run against an already-running Flask application,
run during the ``docker`` tox environment build. **Be warned** that the acceptance tests modify data,
so they should never be run against a real database. This hook is controlled via the
``BIWEEKLYBUDGET_TEST_BASE_URL`` environment variable. If this variable is set, the acceptance
tests will not start a Flask server, but will instead use the specified URL. The URL must not
end with a trailing slash.

Database Migration Tests
++++++++++++++++++++++++

There is a ``migrations`` tox environment that runs `alembic-verify <http://alembic-verify.readthedocs.io/en/latest/>`_
tests on migrations. This tests running through all upgrade migrations in order and then all downgrade migrations
in order, and also tests that the latest (head) migration revision matches the current state of the models.

The environment also runs manually-curated acceptance tests for any migrations that involve data manipulation.

This tox environment is configured via environment variables. Please note that it requires *two* test databases.

* **MYSQL_HOST** - MySQL DB hostname/IP. Defaults to ``127.0.0.1``
* **MYSQL_PORT** - MySQL DB Port. Defaults to ``3306``.
* **MYSQL_USER** - MySQL DB username. Defaults to ``root``.
* **MYSQL_PASS** - MySQL DB password. Defaults to no password.
* **MYSQL_DBNAME_LEFT** - MySQL Database name for the first ("left") test database.
* **MYSQL_DBNAME_RIGHT** - MySQL Database name for the second ("right") test database.

.. _development.alembic:

Alembic DB Migrations
---------------------

This project uses `Alembic <http://alembic.zzzcomputing.com/en/latest/index.html>`_
for DB migrations:

* To generate migrations, run ``alembic -c biweeklybudget/alembic/alembic.ini revision --autogenerate -m "message"`` and examine/edit then commit the resulting file(s). This must be run *before* the model changes are applied to the DB. If adding new models, make sure to import the model class in ``models/__init__.py``.
* To apply migrations, run ``alembic -c biweeklybudget/alembic/alembic.ini upgrade head``.
* To see the current DB version, run ``alembic -c biweeklybudget/alembic/alembic.ini current``.
* To see migration history, run ``alembic -c biweeklybudget/alembic/alembic.ini history``.

Database Debugging
------------------

If you set the ``SQL_ECHO`` environment variable to "true", all SQL run by
SQLAlchemy will be logged at INFO level.

To get an interactive Python shell with the database initialized, use ``python -i bin/db_tester.py``.

Performance Profiling and Logging
---------------------------------

Database
++++++++

If you set the ``SQL_ECHO`` environment variable to "true", all SQL run by SQLAlchemy will be logged at INFO level.

If you set the ``SQL_QUERY_PROFILE`` environment variable to "true", event handlers will be inserted into the SQLAlchemy subsystem that log (at DEBUG level) each query that's run and the time in seconds that the query took to execute. This will also result in logging each query as it is executed.

Flask Application
+++++++++++++++++

When running the application in development mode using ``flask rundev``, the werkzeug WSGI handler will append the time taken to serve each request to the request log, in the format ``[Nms]`` where ``N`` is an integer number of milliseconds.

When running the application in Docker, the time taken to serve the request in decimal seconds will be appended to the end of the Gunicorn access logs, in the format ``[N.Ns]`` where ``N.N`` is the decimal number of seconds.

Docker Image Build
------------------

Use the ``docker`` tox environment. See the docstring at the top of
``biweeklybudget/tests/docker_build.py`` for further information.

Frontend / UI
-------------

The UI is based on `BlackrockDigital's startbootstrap-sb-admin-2 <https://github.com/BlackrockDigital/startbootstrap-sb-admin-2>`_,
currently as of the 3.3.7-1 GitHub release. It is currently not modified at all, but should it need to be rebuilt,
this can be done with: ``pushd biweeklybudget/flaskapp/static/startbootstrap-sb-admin-2 && gulp``

Sphinx also generates documentation for the custom javascript files. This must be done manually
on a machine with `jsdoc <https://jsdoc.app/>`_ installed, via: ``tox -e jsdoc``.

.. _development.vendored_requirements:

Vendored Requirements
---------------------

A number of this project's dependencies are or were seemingly abandoned, and weren't
responding to bugfix pull requests or weren't pushing new releases to PyPI. This made
the installation process painful, as it required ``pip install -r requirements.txt``
to pull in git requirements.

In an attempt to make installation easier, we've vendored any git requirements in to
this repository under ``biweeklybudget/vendored/``. The intent is to move these back
to ``setup.py`` requirements when each project includes the fixes we need in its
official release on PyPI.

To updated the vendored projects:

1. Update ``biweeklybudget/vendored/install_vendored.sh``
2. Run ``cd biweeklybudget/vendored && install_vendored.sh``
3. Ensure that our main ``setup.py`` includes all dependencies of the vendored projects.

Release Checklist
-----------------

Run ``dev/release.py``.
