# Copyright © 2019 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Common setup and fixtures for the pytest suite used by this service."""
import contextlib
from contextlib import contextmanager

import psycopg2
import pytest
import sqlalchemy
from flask_migrate import Migrate, upgrade
from ldclient.integrations.test_data import TestData
from sqlalchemy import event, text

from btr_api import create_app
from btr_api import jwt as _jwt
from btr_api.models import db as _db
from btr_api.config import Testing

def create_test_db(user: str = None,
                   password: str = None,
                   database: str = None,
                   host: str = "localhost",
                   port: int = 1521,
                   database_uri: str = None) -> bool:
    """Create the database in our .devcontainer launched postgres DB.

    Parameters
    ------------
        user: str
            A datbase user that has create database privledges
        password: str
            The users password
        database: str
            The name of the database to create
        host: str, Optional
            The network name of the server
        port: int, Optional
            The numeric port number
    Return
    -----------
        : bool
            If the create database succeeded.
    """
    if database_uri:
        DATABASE_URI = database_uri
    else:
        DATABASE_URI = f"postgresql://{user}:{password}@{host}:{port}/{user}"

    DATABASE_URI = DATABASE_URI[:DATABASE_URI.rfind("/")] + '/postgres'

    try:
        with sqlalchemy.create_engine(DATABASE_URI, isolation_level="AUTOCOMMIT").connect() as conn:
            conn.execute(text(f"CREATE DATABASE {database}"))

        return True
    except sqlalchemy.exc.ProgrammingError as err:
        print(err)  # used in the test suite, so on failure print something
        return False

def drop_test_db(user: str = None,
                   password: str = None,
                   database: str = None,
                   host: str = "localhost",
                   port: int = 1521,
                   database_uri: str = None) -> bool:
    """Delete the database in our .devcontainer launched postgres DB."""
    if database_uri:
        DATABASE_URI = database_uri
    else:
        DATABASE_URI = f"postgresql://{user}:{password}@{host}:{port}/{user}"

    DATABASE_URI = DATABASE_URI[:DATABASE_URI.rfind("/")] + '/postgres'

    close_all = f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{database}'
        AND pid <> pg_backend_pid();
    """
    with contextlib.suppress(sqlalchemy.exc.ProgrammingError,
                             psycopg2.OperationalError,
                             Exception):
        with sqlalchemy.create_engine(DATABASE_URI, isolation_level="AUTOCOMMIT").connect() as conn:
            conn.execute(text(close_all))
            conn.execute(text(f"DROP DATABASE {database}"))

@contextmanager
def not_raises(exception):
    """Corallary to the pytest raises builtin.

    Assures that an exception is NOT thrown.
    """
    try:
        yield
    except exception:
        raise pytest.fail(f'DID RAISE {exception}')


@pytest.fixture(scope='session')
def ld():
    """LaunchDarkly TestData source."""
    td = TestData.data_source()
    yield td


@pytest.fixture(scope='session')
def app(ld):
    """Return a session-wide application configured in TEST mode."""
    _app = create_app('testing', **{'ld_test_data': ld})

    return _app


@pytest.fixture(scope='session')
def client(app):  # pylint: disable=redefined-outer-name
    """Return a session-wide Flask test client."""
    return app.test_client()


@pytest.fixture(scope='session')
def jwt():
    """Return a session-wide jwt manager."""
    return _jwt


@pytest.fixture(scope='session')
def client_ctx(app):  # pylint: disable=redefined-outer-name
    """Return session-wide Flask test client."""
    with app.test_client() as _client:
        yield _client


@pytest.fixture(scope='session')
def db(app):  # pylint: disable=redefined-outer-name, invalid-name
    """Return a session-wide initialised database.

    Drops all existing tables - Meta follows Postgres FKs
    """
    with app.app_context():

        create_test_db(database=app.config.get('DATABASE_TEST_NAME'),
                       database_uri=app.config.get('SQLALCHEMY_DATABASE_URI'))

        sess = _db.session()
        sess.execute(text("SET TIME ZONE 'UTC';"))

        migrate = Migrate(app,
                _db,
                **{'dialect_name': 'postgres'})
        upgrade()

        yield _db

        drop_test_db(database=app.config.get('DATABASE_TEST_NAME'),
                     database_uri=app.config.get('SQLALCHEMY_DATABASE_URI'))


@pytest.fixture(scope='function')
def session(app, db):  # pylint: disable=redefined-outer-name, invalid-name
    """Return a function-scoped session."""
    with app.app_context():
        conn = db.engine.connect()
        txn = conn.begin()

        try:
            options = dict(bind=conn, binds={})
            # sess = db.create_scoped_session(options=options)
            sess = db._make_scoped_session(options=options)
        except Exception as err:
            print(err)
            print('done')

        # establish  a SAVEPOINT just before beginning the test
        # (http://docs.sqlalchemy.org/en/latest/orm/session_transaction.html#using-savepoint)
        sess.begin_nested()

        @event.listens_for(sess(), 'after_transaction_end')
        def restart_savepoint(sess2, trans):  # pylint: disable=unused-variable
            # Detecting whether this is indeed the nested transaction of the test
            if trans.nested and not trans._parent.nested:  # pylint: disable=protected-access
                # Handle where test DOESN'T session.commit(),
                sess2.expire_all()
                sess.begin_nested()

        db.session = sess

        sql = text('select 1')
        sess.execute(sql)

        yield sess

        # Cleanup
        sess.remove()
        # This instruction rollsback any commit that were executed in the tests.
        txn.rollback()
        conn.close()
