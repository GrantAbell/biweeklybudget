"""
The latest version of this package is available at:
<http://github.com/jantman/biweeklybudget>

################################################################################
Copyright 2016 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of biweeklybudget, also known as biweeklybudget.

    biweeklybudget is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    biweeklybudget is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with biweeklybudget.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/biweeklybudget> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import biweeklybudget.settings
import socket
from biweeklybudget.tests.fixtures.sampledata import SampleDataLoader
try:
    from pytest_flask.fixtures import LiveServer
except ImportError:
    pass

connstr = os.environ.get('DB_CONNSTRING', None)
if connstr is None:
    connstr = 'mysql+pymysql://budgetTester:jew8fu0ue@127.0.0.1:3306/' \
              'budgettest?charset=utf8mb4'
    os.environ['DB_CONNSTRING'] = connstr
biweeklybudget.settings.DB_CONNSTRING = connstr

import biweeklybudget.db  # noqa
import biweeklybudget.models.base  # noqa
from biweeklybudget.flaskapp.app import app  # noqa

engine = create_engine(connstr)


@pytest.fixture(scope="session")
def testdb():
    """
    This fixture handles the overall DB setup.
    """
    # setup the connection
    conn = engine.connect()
    if 'NO_REFRESH_DB' not in os.environ:
        # clean the database
        biweeklybudget.models.base.Base.metadata.reflect(engine)
        biweeklybudget.models.base.Base.metadata.drop_all(engine)
        biweeklybudget.models.base.Base.metadata.create_all(engine)
        # load the sample data
        data_sess = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=conn)
        )
        SampleDataLoader(data_sess).load()
        data_sess.flush()
        data_sess.commit()
        data_sess.close()
    # create a session to use for the tests
    sess = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=conn)
    )
    # yield the session
    yield(sess)
    # when we're done, close
    sess.close()
    conn.close()


@pytest.fixture(scope="class")
def class_scoped_db():
    """
    This fixture rolls the DB back to the previous state when the class is
    finished; to be used on classes that alter data.

    Use like:

        @pytest.mark.usefixtures('class_scoped_db', 'testdb')
        class MyClass(AcceptanceHelper):
    """
    # setup the connection
    conn = engine.connect()
    sess = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=conn)
    )
    # yield the session
    yield(sess)
    sess.close()
    # clean the database
    biweeklybudget.models.base.Base.metadata.reflect(engine)
    biweeklybudget.models.base.Base.metadata.drop_all(engine)
    biweeklybudget.models.base.Base.metadata.create_all(engine)
    # load the sample data
    data_sess = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=conn)
    )
    SampleDataLoader(data_sess).load()
    data_sess.flush()
    data_sess.commit()
    data_sess.close()
    # when we're done, close
    conn.close()


@pytest.fixture(scope="session")
def testflask():
    """
    This is a version of pytest-flask's live_server fixture, modified for
    session use.
    """
    # Bind to an open port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()

    server = LiveServer(app, port)
    server.start()
    yield(server)
    server.stop()


@pytest.fixture(scope="session")
def base_url(testflask):
    """
    Simple fixture to return ``testflask`` base URL
    """
    return testflask.url()


@pytest.fixture
def selenium(selenium):
    """
    Per pytest-selenium docs, use this to override the selenium fixture to
    provide global common setup.
    """
    selenium.set_window_size(1200, 800)
    selenium.implicitly_wait(2)
    # from http://stackoverflow.com/a/13853684/211734
    selenium.set_script_timeout(60)
    # from http://stackoverflow.com/a/17536547/211734
    selenium.set_page_load_timeout(60)
    return selenium
