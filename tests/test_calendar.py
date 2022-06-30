from copy import deepcopy
import pytest

from scripts.fantasy_calendar import Date, Calendar

@pytest.fixture(params=[
    (1, 1, 1),
    (2015, 2, 2),
    (100, 4, 30),
    (10, 3, 1),
    (0, 2, 23),
    (-1, 2, 12),
    (10, 7, 30),
])
def some_date(request):
    return Date(*request.param)

@pytest.fixture(params=[
    ((1, 1, 1), (2, 1, 1)),
    ((1, 1, 1), (1, 2, 1)),
    ((1, 1, 1), (1, 1, 2)),
    ((-1, 1, 1), (0, 1, 1)),
    ((-2, 1, 1), (-1, 1, 1)),
])
def early_vs_late_date(request):
    return tuple(Date(*p) for p in request.param)

@pytest.fixture
def months():
    return [
        {
            "name": "first month",
            "days": 30
        },
        {
            "name": "second month",
            "days": 30
        },
        {
            "name": "first special day",
            "days": 1
        },
        {
            "name": "third month",
            "days": 30
        },
        {
            "name": "second special day",
            "days": 1
        },
        {
            "name": "third special day",
            "days": 1
        },
        {
            "name": "final month",
            "days": 30
        }
    ]

@pytest.fixture
def today():
    return "12th of third month 17"

@pytest.fixture
def calendar(months, today):
    return Calendar(months, today, "before", "after", False)

@pytest.mark.parametrize("early, late", [
    (Date(1, 1, 1), Date(2, 1, 1)),
    (Date(1, 1, 1), Date(1, 2, 1)),
    (Date(1, 1, 1), Date(1, 1, 2)),
    (Date(-1, 1, 1), Date(0, 1, 1)),
    (Date(-2, 1, 1), Date(-1, 1, 1)),
])
def test_date_unequal(early, late):
    assert early < late and early <= late and late > early and late >= early

def test_date_equal(some_date):
    assert some_date == deepcopy(some_date)

def test_date_not_equal(some_date):
    assert some_date != Date(1337, 3, 14)


def test_calendar_verify_date(calendar, some_date):
    assert calendar.verify_date(some_date)

@pytest.mark.parametrize("date, text", [
    (Date(1, 1, 1), "1st of first month 1 after"),
    (Date(2015, 2, 2), "2nd of second month 2015 after"),
    (Date(100, 4, 30), "30th of third month 100 after"),
    (Date(10, 3, 1), "1st of first special day 10 after"),
    (Date(0, 2, 23), "23rd of second month 1 before"),
    (Date(-1, 2, 12), "12th of second month 2 before"),
    (Date(10, 7, 30), "30th of final month 10 after"),
])
class TestCalendarString:
    def test_date_from_string(self, calendar, date, text):
        assert calendar.date_from_string(text) == date
    
    def test_string_from_date(self, calendar, date, text):
        assert calendar.string_from_date(date) == text