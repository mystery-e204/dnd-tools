from copy import deepcopy
import pytest

from scripts.fantasy_calendar import Date, Calendar

@pytest.fixture(params=[
    (1, 1, 1),
    (2015, 2, 2),
    (100, 3, 30),
    (10, 3, 1),
    (-1, 2, 23),
    (-2, 2, 12),
])
def some_date(request):
    return request.param

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
            "name": "third month",
            "days": 30
        },
    ]

@pytest.fixture
def holidays():
    return [
        {
            "name": "first special day",
            "month": 1,
            "day": 3
        },
        {
            "name": "second special day",
            "month": 3,
            "day": 9
        },
        {
            "name": "third special day",
            "month": 3,
            "day": 30
        }
    ]

@pytest.fixture
def today():
    return "12th of third month 17"

@pytest.fixture
def calendar(months, holidays, today):
    return Calendar(months, today, "before", "after", False, holidays)


def test_calendar_verify_date(calendar, some_date):
    assert calendar.verify_date(some_date)

def test_calendar_days_per_year(calendar):
    assert calendar.days_per_year == 90

@pytest.mark.parametrize("date, text, timestamp", [
    ((1, 1, 1), "1st of first month 1 after", 0),
    ((2015, 2, 2), "2nd of second month 2015 after", 181291),
    ((10, 1, 3), "first special day 10 after", 812),
    ((100, 3, 30), "third special day 100 after", 8999),
    ((-1, 2, 23), "23rd of second month 1 before", -38),
    ((-2, 2, 12), "12th of second month 2 before", -139),
])
class TestCalendar:
    def test_timestamp_to_date(self, calendar: Calendar, date: Date, text: str, timestamp: int):
        assert calendar.timestamp_to_date(timestamp) == date
    
    def test_date_to_timestamp(self, calendar: Calendar, date: Date, text: str, timestamp: int):
        assert calendar.date_to_timestamp(date) == timestamp
    
    def test_timestamp_to_str(self, calendar: Calendar, date: Date, text: str, timestamp: int):
        assert calendar.timestamp_to_str(timestamp) == text
    
    def test_str_to_timestamp(self, calendar: Calendar, date: Date, text: str, timestamp: int):
        assert calendar.str_to_timestamp(text) == timestamp

