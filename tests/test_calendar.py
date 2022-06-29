from copy import deepcopy
import pytest

from scripts.fantasy_calendar import Date, Calendar

@pytest.fixture(params=[
    (1, 1, 1),
    (2015, 2, 17),
    (100, 4, 30),
    (10, 3, 1),
    (0, 2, 5),
    (-1, 2, 10),
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

def test_date_less_than(early_vs_late_date):
    assert (
        early_vs_late_date[0] < early_vs_late_date[1] and
        early_vs_late_date[0] <= early_vs_late_date[1]
    )

def test_date_greater_than(early_vs_late_date):
    assert (
        early_vs_late_date[1] > early_vs_late_date[0] and
        early_vs_late_date[1] >= early_vs_late_date[0]
    )

def test_date_equal(some_date):
    assert some_date == deepcopy(some_date)

def test_date_not_equal(some_date):
    assert some_date != Date(1337, 3, 14)


def test_calendar_verify_date(calendar, some_date):
    assert calendar.verify_date(some_date)