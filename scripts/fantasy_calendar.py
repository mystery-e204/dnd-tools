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
        today: str | Timestamp,
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
        year, day = divmod(timestamp, self.days_per_year)
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
        timestamp = year * self.days_per_year + day - 1
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
    def days_per_year(self):
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

    def day_of_year(self, timestamp: Timestamp) -> int:
        year, _, _ = self.timestamp_to_date(timestamp)
        return timestamp - self.date_to_timestamp((year, 1, 1)) + 1

    def rest_of_month(self, timestamp: Timestamp) -> int:
        _, month, day = self.timestamp_to_date(timestamp)
        return self._months[month - 1]["days"] - day

    def rest_of_year(self, timestamp: Timestamp) -> int:
        year, _, _ = self.timestamp_to_date(timestamp + self.days_per_year)
        return self.date_to_timestamp((year, 1, 1)) - timestamp - 1


def load_calendar(json_file) -> Calendar:
    calendar_data = json.load(json_file)
    return Calendar(*[calendar_data[key] for key in ["months", "today", "before", "after", "hasYearZero"]])

def add_command(sub_parsers, name: str, callback: Callable[[Calendar, argparse.Namespace], Any]) -> argparse.ArgumentParser:
    parser = sub_parsers.add_parser(name)
    parser.set_defaults(callback=callback)
    return parser

def add_command_get_age(sub_parsers):
    def callback(calendar: Calendar, args: argparse.Namespace):
        birth_timestamp = calendar.str_to_timestamp(args.birthday)
        if calendar.today < birth_timestamp:
            print("Not yet born")
        else:
            print((birth_timestamp - calendar.today) / calendar.days_per_year)

    parser = add_command(sub_parsers, "get-age", callback)
    parser.add_argument("birthday")

def add_command_get_birthday(sub_parsers):
    def callback(calendar: Calendar, args: argparse.Namespace):
        print(calendar.today - args.age * calendar.days_per_year - randint(0, calendar.days_per_year - 1))

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
