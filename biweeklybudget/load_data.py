"""
The latest version of this package is available at:
<http://github.com/jantman/biweeklybudget>

################################################################################
Copyright 2016-2024 Jason Antman <http://www.jasonantman.com>

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

import argparse
import logging
import atexit
import importlib

from biweeklybudget.db import init_db, cleanup_db, db_session, engine
from biweeklybudget.cliutils import set_log_debug, set_log_info
from biweeklybudget.models.base import Base

logger = logging.getLogger(__name__)


def parse_args():
    default_mod = 'biweeklybudget.tests.fixtures.sampledata'
    default_cls = 'SampleDataLoader'
    p = argparse.ArgumentParser(description='Load initial data to DB')
    p.add_argument('-v', '--verbose', dest='verbose', action='count', default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-m', '--data-module', dest='modname', action='store',
                   type=str, default=default_mod,
                   help='data fixture module (default: %s)' % default_mod)
    p.add_argument('-c', '--data-class', dest='clsname', action='store',
                   type=str, default=default_cls,
                   help='data fixture class (default: %s)' % default_cls)
    args = p.parse_args()
    return args


def main():
    global logger
    logging.basicConfig(
        level=logging.WARNING,
        format="[%(asctime)s %(levelname)s] %(message)s"
    )
    logger = logging.getLogger()

    args = parse_args()

    # set logging level
    if args.verbose > 1:
        set_log_debug(logger)
    elif args.verbose == 1:
        set_log_info(logger)

    atexit.register(cleanup_db)
    Base.metadata.reflect(engine)
    Base.metadata.drop_all(engine)
    db_session.flush()
    db_session.commit()
    init_db()

    logger.info('Loading data from: %s.%s', args.modname, args.clsname)
    klass = getattr(importlib.import_module(args.modname), args.clsname)
    inst = klass(db_session)
    logger.info('Loading data')
    inst.load()
    db_session.commit()
    logger.info('Data loaded.')


if __name__ == "__main__":
    main()
