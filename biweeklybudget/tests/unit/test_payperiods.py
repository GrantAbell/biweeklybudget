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

import sys
import pytest
from datetime import datetime, date, timedelta
from sqlalchemy.orm.session import Session

from biweeklybudget.payperiods import BiweeklyPayPeriod
from biweeklybudget.models.ofx_transaction import OFXTransaction
from biweeklybudget.models.transaction import Transaction
from biweeklybudget.models.scheduled_transaction import ScheduledTransaction
from biweeklybudget.tests.unit_helpers import binexp_to_dict

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import Mock, patch, call
else:
    from unittest.mock import Mock, patch, call

pbm = 'biweeklybudget.payperiods'
pb = '%s.BiweeklyPayPeriod' % pbm


class TestBiweeklyPayPeriod(object):

    def setup(self):
        self.cls = BiweeklyPayPeriod(date(2017, 3, 17))

    def test_init(self):
        cls = BiweeklyPayPeriod(date(2017, 3, 17))
        assert cls._start_date == date(2017, 3, 17)
        assert cls._end_date == date(2017, 3, 30)

    def test_init_datetime(self):
        cls = BiweeklyPayPeriod(datetime(2017, 3, 17))
        assert cls._start_date == date(2017, 3, 17)
        assert cls._end_date == date(2017, 3, 30)

    def test_period_interval(self):
        assert self.cls.period_interval == timedelta(days=14)

    def test_period_length(self):
        assert self.cls.period_length == timedelta(days=13)

    def test_start_date(self):
        assert self.cls.start_date == date(2017, 3, 17)

    def test_end_date(self):
        assert self.cls.end_date == date(2017, 3, 30)

    def test_next(self):
        assert self.cls.next == BiweeklyPayPeriod(date(2017, 3, 31))

    def test_previous(self):
        assert self.cls.previous == BiweeklyPayPeriod(date(2017, 3, 3))

    def test_period_for_date(self):
        assert BiweeklyPayPeriod.period_for_date(
            date(2017, 3, 16)) == BiweeklyPayPeriod(date(2017, 3, 3))
        assert BiweeklyPayPeriod.period_for_date(
            date(2017, 3, 17)) == BiweeklyPayPeriod(date(2017, 3, 17))
        assert BiweeklyPayPeriod.period_for_date(
            date(2017, 3, 18)) == BiweeklyPayPeriod(date(2017, 3, 17))
        assert BiweeklyPayPeriod.period_for_date(
            date(2017, 3, 30)) == BiweeklyPayPeriod(date(2017, 3, 17))
        assert BiweeklyPayPeriod.period_for_date(
            date(2017, 3, 31)) == BiweeklyPayPeriod(date(2017, 3, 31))
        assert BiweeklyPayPeriod.period_for_date(
            date(2017, 1, 21)) == BiweeklyPayPeriod(date(2017, 1, 20))
        assert BiweeklyPayPeriod.period_for_date(
            date(2017, 5, 2)) == BiweeklyPayPeriod(date(2017, 4, 28))

    def test_repr(self):
        assert str(self.cls) == '<BiweeklyPayPeriod(2017-03-17)>'

    @pytest.mark.skipif(sys.version_info[0] >= 3, reason='py2 only')
    def test_ordering_py27(self):
        assert self.cls < BiweeklyPayPeriod(date(2017, 4, 16))
        assert self.cls > BiweeklyPayPeriod(date(2017, 2, 13))
        assert self.cls == BiweeklyPayPeriod(date(2017, 3, 17))
        self.cls < 2
        self.cls.__eq__(2)

    @pytest.mark.skipif(sys.version_info[0] < 3, reason='py3 only')
    def test_ordering_py3(self):
        assert self.cls < BiweeklyPayPeriod(date(2017, 4, 16))
        assert self.cls > BiweeklyPayPeriod(date(2017, 2, 13))
        assert self.cls == BiweeklyPayPeriod(date(2017, 3, 17))
        with pytest.raises(TypeError):
            self.cls < 2
        self.cls.__eq__(2)

    def test_filter_query(self):
        q = Mock()
        res = self.cls.filter_query(q, OFXTransaction.date_posted)
        kall = q.mock_calls[0]
        assert kall[0] == 'filter'
        a = OFXTransaction.date_posted >= self.cls.start_date
        b = OFXTransaction.date_posted <= self.cls.end_date
        assert kall[1][0].compare(a) is True
        assert kall[1][1].compare(b) is True
        assert res == q.filter.return_value

    def test_transactions(self):
        mock_sess = Mock(spec_set=Session)
        mock_res = Mock()
        with patch('%s.filter_query' % pb, autospec=True) as mock_filter:
            mock_filter.return_value = mock_res
            res = self.cls.transactions(mock_sess)
        assert res == mock_res
        assert mock_filter.mock_calls == [
            call(self.cls, mock_sess.query.return_value, Transaction.date)
        ]
        assert mock_sess.mock_calls == [
            call.query(Transaction)
        ]

    def test_scheduled_transactions_date(self):
        mock_sess = Mock(spec_set=Session)
        mock_res = Mock()
        with patch('%s.filter_query' % pb, autospec=True) as mock_filter:
            mock_filter.return_value = mock_res
            res = self.cls.scheduled_transactions_date(mock_sess)
        assert res == mock_res
        assert mock_filter.mock_calls == [
            call(
                self.cls,
                mock_sess.query.return_value,
                ScheduledTransaction.date
            )
        ]
        assert mock_sess.mock_calls == [
            call.query(ScheduledTransaction)
        ]

    def test_scheduled_transactions_per_period(self):
        mock_sess = Mock(spec_set=Session)
        res = self.cls.scheduled_transactions_per_period(mock_sess)
        assert res == mock_sess.query.return_value.filter.return_value
        assert mock_sess.mock_calls[0] == call.query(ScheduledTransaction)
        kall = mock_sess.mock_calls[1]
        assert kall[0] == 'query().filter'
        expected = ScheduledTransaction.schedule_type.__eq__('per period')
        assert binexp_to_dict(expected) == binexp_to_dict(kall[1][0])

    def test_scheduled_transactions_monthly_contiguous(self):
        cls = BiweeklyPayPeriod(date(2017, 3, 2))
        mock_sess = Mock(spec_set=Session)
        res = cls.scheduled_transactions_monthly(mock_sess)
        assert res == mock_sess.query.return_value.filter.return_value
        assert mock_sess.mock_calls[0] == call.query(ScheduledTransaction)
        kall = mock_sess.mock_calls[1]
        assert kall[0] == 'query().filter'
        expected = [
            ScheduledTransaction.schedule_type.__eq__('monthly'),
            ScheduledTransaction.day_of_month.__le__(15),
            ScheduledTransaction.day_of_month.__ge__(2)
        ]
        for idx, exp in enumerate(expected):
            assert binexp_to_dict(kall[1][idx]) == binexp_to_dict(exp)

    def test_scheduled_transactions_monthly_crossmonth(self):
        cls = BiweeklyPayPeriod(date(2017, 3, 24))
        mock_sess = Mock(spec_set=Session)
        mock_or_result = Mock()
        with patch('%s.or_' % pbm) as mock_or:
            mock_or.return_value = mock_or_result
            res = cls.scheduled_transactions_monthly(mock_sess)
        assert res == mock_sess.query.return_value.filter.return_value
        assert mock_sess.mock_calls[0] == call.query(ScheduledTransaction)
        kall = mock_sess.mock_calls[1]
        assert kall[0] == 'query().filter'
        expected = ScheduledTransaction.schedule_type.__eq__('monthly')
        assert binexp_to_dict(kall[1][0]) == binexp_to_dict(expected)
        assert kall[1][1] == mock_or_result
        kall = mock_or.mock_calls[0]
        assert len(mock_or.mock_calls) == 1
        expected = [
            ScheduledTransaction.day_of_month.__le__(6),
            ScheduledTransaction.day_of_month.__ge__(24)
        ]
        for idx, exp in enumerate(expected):
            assert binexp_to_dict(kall[1][idx]) == binexp_to_dict(exp)
