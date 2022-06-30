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

def test_calendar_num_days_of_year(calendar):
    assert calendar.num_days_of_year == 123

@pytest.mark.parametrize("date, text, day, left_month, left_year", [
    (Date(1, 1, 1), "1st of first month 1 after", 1, 29, 122),
    (Date(2015, 2, 2), "2nd of second month 2015 after", 32, 28, 91),
    (Date(100, 4, 30), "30th of third month 100 after", 91, 0, 32),
    (Date(10, 3, 1), "1st of first special day 10 after", 61, 0, 62),
    (Date(0, 2, 23), "23rd of second month 1 before", 53, 7, 70),
    (Date(-1, 2, 12), "12th of second month 2 before", 42, 18, 81),
    (Date(10, 7, 30), "30th of final month 10 after", 123, 0, 0),
])
class TestCalendar:
    def test_date_from_string(self, calendar, date, text, day, left_month, left_year):
        assert calendar.date_from_string(text) == date
    
    def test_string_from_date(self, calendar, date, text, day, left_month, left_year):
        assert calendar.string_from_date(date) == text

    def test_day_of_year(self, calendar, date, text, day, left_month, left_year):
        assert calendar.day_of_year(date) == day

    def test_remainder_of_month(self, calendar, date, text, day, left_month, left_year):
        assert calendar.remainder_of_month(date) == left_month

    def test_remainder_of_year(self, calendar, date, text, day, left_month, left_year):
        assert calendar.remainder_of_year(date) == left_year

@pytest.mark.parametrize("date1, shift, date2", [
    (Date(1, 1, 1), 13, Date(1, 1, 14)),
    (Date(-3, 2, 2), 246, Date(-1, 2, 2)),
    (Date(10, 7, 10), -50, Date(10, 2, 23)),
    (Date(10, 2, 10), -250, Date(8, 2, 6)),
])
def test_calendar_shift(calendar, date1, shift, date2):
    assert calendar.shifted_date(date1, shift) == date2
