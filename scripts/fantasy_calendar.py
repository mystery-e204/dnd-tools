#!/usr/bin/env python3

from __future__ import annotations

import json
import argparse
from random import randint
from typing import Any, TypedDict, Callable
import re

PATTERN_SLASH_DATE = re.compile(r"^(\d+)\/(\d+)\/(\d+) *(\w+)?$")
PATTERN_WORDED_DATE = re.compile(r"^(\d+)(st|nd|rd|th) +of +(\D+\S) +(\d+) *(\w+)?$")
PATTERN_SPECIAL_DATE = re.compile(r"^(.*) (\d+) *(\w+)?$")

Timestamp = int
Date = tuple[int, int, int]

class Month(TypedDict):
    name: str
    days: int

class Holiday(TypedDict):
    name: str
    month: int
    day: int

def nth_from_day(day: int) -> str:
    if day < 0:
        raise ValueError("Day must not be negative")
    ones_digit = day % 10
    tens_digit = (day // 10) % 10
    if tens_digit == 1: suffix = "th"
    elif ones_digit == 1: suffix = "st"
    elif ones_digit == 2: suffix = "nd"
    elif ones_digit == 3: suffix = "rd"
    else: suffix = "th"
    return f"{day}{suffix}"


class Calendar():
    def __init__(self,
        months: list[Month],
        today: str|Timestamp,
        before: str,
        after: str,
        has_year_zero: bool,
        holidays: list[Holiday] = [],
        day_zero: Timestamp = 0
    ) -> None:
        self._months = months
        self._before = before
        self._after = after
        self._has_year_zero = has_year_zero
        self._holidays = holidays
        self._day_zero = day_zero
        self.today = today if isinstance(today, Timestamp) else self.str_to_timestamp(today)
        
    def timestamp_to_date(self, timestamp: Timestamp) -> Date:
        timestamp -= self._day_zero
        year, day = divmod(timestamp, self.num_days_of_year)
        day += 1
        month = 1
        for m in self._months:
            if day > m["days"]:
                day -= m["days"]
                month += 1
            else:
                break
        year += int(year >= 0 or self._has_year_zero)
        return year, month, day

    def date_to_timestamp(self, date: Date) -> Timestamp:
        if not self.verify_date(date):
            raise ValueError(f"Date {date} does not exist in calendar")
        year, month, day = date
        year -= int(year >= 0 or self._has_year_zero)
        timestamp = year * self.num_days_of_year + day - 1
        for m in self._months[: month - 1]:
            timestamp += m["days"]
        timestamp += self._day_zero
        return Timestamp(timestamp)

    def str_to_timestamp(self, s: str) -> Timestamp:
        # Dates like 23/7/1978
        if matched := re.match(PATTERN_SLASH_DATE, s):
            day, month, year, before_or_after = matched.groups()
            day, month, year = map(int, (day, month, year))
        # Dates like 23rd of July 1978
        elif matched := re.match(PATTERN_WORDED_DATE, s):
            day, suffix, month, year, before_or_after = matched.groups()
            day = int(day)
            month, _ = self._search_month(month)
            year = int(year)
        # Special days inbetween months
        elif matched := re.match(PATTERN_SPECIAL_DATE, s):
            name, year, before_or_after = matched.groups()
            holiday = self._search_holiday(name)
            day = holiday["day"]
            month = holiday["month"]
            year = int(year)

        if before_or_after:
            if before_or_after == self._before:
                year = -year
            elif before_or_after != self._after:
                raise Exception(f"Token {before_or_after} not recognized as before or after")

        return self.date_to_timestamp((year, month, day))

    def timestamp_to_str(self, timestamp: Timestamp) -> str:
        year, month, day = self.timestamp_to_date(timestamp)
        year_str = f"{abs(year)}"
        before_or_after = self._before if year < 0 else self._after

        if holiday_str := self._try_get_holiday(month, day):
            return f"{holiday_str} {year_str} {before_or_after}"
        else:
            day_str = nth_from_day(day)
            month_str = self._months[month - 1]["name"]
            return f"{day_str} of {month_str} {year_str} {before_or_after}"

    def verify_date(self, date: Date) -> bool:
        year, month, day = date
        year_ok = self._has_year_zero or year != 0
        month_ok = month > 0 and month <= len(self._months)
        day_ok = day > 0 and day <= self._months[month - 1]["days"]
        return year_ok and month_ok and day_ok

    @property
    def num_days_of_year(self):
        return sum(month["days"] for month in self._months)

    def _search_month(self, month_name: str) -> tuple[int, Month]:
        for num, month in enumerate(self._months, 1):
            if month["name"] == month_name:
                return num, month
        raise Exception(f"Month {month_name} not found in calendar")

    def _search_holiday(self, holiday_name: str) -> Holiday:
        for holiday in self._holidays:
            if holiday["name"] == holiday_name:
                return holiday
        raise Exception(f"Holiday {holiday_name} not found in calendar")

    def _try_get_holiday(self, month: int, day: int) -> str | None:
        for holiday in self._holidays:
            if holiday["month"] == month and holiday["day"] == day:
                return holiday["name"]
        return None

    def _day_of_year(self, date: Date) -> int:
        return date.day + sum(month["days"] for month in self._months[: date.month - 1])

    def day_of_year(self, date: Date) -> int:
        if not self.verify_date(date): raise DateError(date)
        return self._day_of_year(date)

    def _remainder_of_month(self, date: Date) -> int:
        return self._months[date.month - 1]["days"] - date.day

    def remainder_of_month(self, date: Date) -> int:
        if not self.verify_date(date): raise DateError(date)
        return self._remainder_of_month(date)

    def _remainder_of_year(self, date: Date) -> int:
        return self._remainder_of_month(date) + sum(month["days"] for month in self._months[date.month :])

    def remainder_of_year(self, date: Date) -> int:
        if not self.verify_date(date): raise DateError(date)
        return self._remainder_of_year(date)

    def _shifted_date(self, date: Date, days: int) -> Date:
        shifted_date = Date(date.year, date.month, date.day)

        if days == 0:
            return shifted_date
        elif days > 0:
            years, days = divmod(days, self.num_days_of_year)
            shifted_date.year += years

            remainder = self._remainder_of_year(shifted_date)
            if days > remainder:
                days -= remainder + 1
                shifted_date.year += 1
                shifted_date.month = 1
                shifted_date.day = 1

            for month in self._months:
                if days >= month["days"]:
                    days -= month["days"]
                    shifted_date.month += 1
                else:
                    shifted_date.day += days
                    return shifted_date
        else:
            years, days = divmod(-days, self.num_days_of_year)
            shifted_date.year -= years

            remainder = self._day_of_year(shifted_date)
            if days >= remainder:
                days -= remainder
                shifted_date.year -= 1
                shifted_date.month = len(self._months)
                shifted_date.day = self._months[-1]["days"]

            for month in self._months[-1::-1]:
                if days >= month["days"]:
                    days -= month["days"]
                    shifted_date.month -= 1
                else:
                    shifted_date.day -= days
                    return shifted_date


    def shifted_date(self, date: Date, days: int) -> Date:
        if not self.verify_date(date): raise DateError(date)
        return self._shifted_date(date, days)

    def _days_between_dates(self, date1: Date, date2: Date) -> int:
        reverse = False
        if date1 == date2:
            return 0
        elif date2 < date1:
            date1, date2 = date2, date1
            reverse = True

        diff_years = date2.year - date1.year
        if diff_years > 0:
            days = self._remainder_of_year(date1) + self._day_of_year(date2)
            days += (diff_years - 1) * self.num_days_of_year
        elif date2.month > date1.month:
            days = self._remainder_of_month(date1) + date2.day
            days += sum(month["days"] for month in self._months[date1.month : date2.month])
        else:
            days = date2.day - date1.day

        return -days if reverse else days

    def days_between_dates(self, date1: Date, date2: Date) -> int:
        if not self.verify_date(date1): raise DateError(date1)
        if not self.verify_date(date2): raise DateError(date2)
        return self._days_between_dates(date1, date2)

    def _get_random_date(self, start: Date, stop: Date) -> Date:
        if start == stop:
            return Date(start.year, start.month, start.day)
        if start > stop:
            raise Exception(f"{start} is ahead of {stop}")

        num_days = self._days_between_dates(start, stop)
        shift = randint(0, num_days - 1)
        return self._shifted_date(start, shift)

    def get_random_date(self, start: Date = None, stop: Date = None) -> Date:
        if start is None and stop is None:
            shift = randint(0, self.num_days_of_year - 1)
            return self._shifted_date(Date(self.today.year, 1, 1), shift)
        else:
            # From the start of the year
            if start is None:
                start = Date(stop.year, 1, 1)
            elif not self.verify_date(start):
                raise DateError(start)
            # Till the end of the year
            if stop is None:
                stop = Date(start.year, len(self._months), self._months[-1]["days"])
            elif not self.verify_date(stop):
                raise DateError(stop)

            return self._get_random_date(start, stop)

def load_calendar(json_file) -> Calendar:
    calendar_data = json.load(json_file)
    return Calendar(*[calendar_data[key] for key in ["months", "today", "before", "after", "hasYearZero"]])

def add_command(sub_parsers, name: str, callback: Callable[[Calendar, argparse.Namespace], Any]) -> argparse.ArgumentParser:
    parser = sub_parsers.add_parser(name)
    parser.set_defaults(callback=callback)
    return parser

def add_command_get_age(sub_parsers):
    def callback(calendar: Calendar, args: argparse.Namespace):
        birthdate = calendar.date_from_string(args.birthday)
        age = calendar.today.year - birthdate.year
        if age < 0:
            print("Not yet born")
        else:
            if calendar.today.month < birthdate.month or calendar.today.month == birthdate.month and calendar.today.day < birthdate.day:
                age -= 1
            print(age)

    parser = add_command(sub_parsers, "get-age", callback)
    parser.add_argument("birthday")

def add_command_get_birthday(sub_parsers):
    def callback(calendar: Calendar, args: argparse.Namespace):
        birthday = calendar.get_random_date()
        birthday.year -= args.age + int(birthday > calendar.today)
        print(calendar.string_from_date(birthday))

    parser = add_command(sub_parsers, "get-birthday", callback)
    parser.add_argument("age", type=int)

if __name__ == "__main__":
    main_parser = argparse.ArgumentParser()
    main_parser.add_argument("calendar", type=argparse.FileType("r"))

    sub_parsers = main_parser.add_subparsers()
    sub_parsers.required = True

    add_command_get_age(sub_parsers)
    add_command_get_birthday(sub_parsers)

    args = main_parser.parse_args()

    calendar = load_calendar(args.calendar)
    args.callback(calendar, args)
