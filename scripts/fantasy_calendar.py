#!/usr/bin/env python3

from __future__ import annotations

import json
import argparse
from random import randint
from typing import Any, List, TypedDict, Callable
import re

PATTERN_SLASH_DATE = re.compile(r"^(\d+)\/(\d+)\/(\d+) *(\w+)?$")
PATTERN_WORDED_DATE = re.compile(r"^(\d+)(st|nd|rd|th) +of +(\D+\S) +(\d+) *(\w+)?$")
PATTERN_SPECIAL_DATE = re.compile(r"^(.*) (\d+) *(\w+)?$")

class Month(TypedDict):
    name: str
    days: int

class Date():
    def __init__(self, year: int, month: int, day: int) -> None:
        if month < 1: raise ValueError("Month must be positive")
        if day < 1: raise ValueError("Day must be positive")
        self.year = year
        self.month = month
        self.day = day

    def __str__(self) -> str:
        return f"Date({self.year}, {self.month}, {self.day})"

    def __eq__(self, other: Date) -> bool:
        return self.day == other.day and self.month == other.month and self.year == other.year

    def __lt__(self, other: Date) -> bool:
        return (
            self.year < other.year or
            self.year == other.year and (
                self.month < other.month or
                self.month == other.month and self.day < other.day
            )
        )

    def __le__(self, other: Date) -> bool:
        return self < other or self == other

    def __gt__(self, other: Date) -> bool:
        return not self <= other

    def __ge__(self, other: Date) -> bool:
        return not self < other
        

class DateError(Exception):
    def __init__(self, date: Date):
        message = f"{date} is not a valid date"
        super().__init__(message)


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
    def __init__(self, months: List[Month], today: str, before: str, after: str, has_year_zero: bool) -> None:
        self._months = months
        self._before = before
        self._after = after
        self._has_year_zero = has_year_zero
        self.today = self.date_from_string(today)
        
    def date_from_string(self, s: str) -> Date:
        # Dates like 23/7/1978
        if matched := re.match(PATTERN_SLASH_DATE, s):
            day, month, year, before_or_after = matched.groups()
            day, month, year = map(int, (day, month, year))
        # Dates like 23rd of July 1978
        elif matched := re.match(PATTERN_WORDED_DATE, s):
            day, suffix, month, year, before_or_after = matched.groups()
            day = int(day)
            month = self._get_month_num(month)
            year = int(year)
        # Special days inbetween months
        elif matched := re.match(PATTERN_SPECIAL_DATE, s):
            name, year, before_or_after = matched.groups()
            day = 1
            month = self._get_month_num(name)
            year = int(year)

        if before_or_after:
            if before_or_after == self._before:
                year = -year + int(not self._has_year_zero)
            elif before_or_after != self._after:
                raise Exception(f"Token {before_or_after} not recognized as before or after")

        date = Date(year, month, day)
        if not self.verify_date(date): raise DateError(date)
        return date

    def string_from_date(self, date: Date) -> str:
        if not self.verify_date(date): raise DateError(date)

        year = date.year - int(date.year < 1 and not self._has_year_zero)
        before_or_after = self._before if year < 0 else self._after
        year = abs(year)
        day_str = nth_from_day(date.day)
        month_str = self._months[date.month - 1]["name"]

        return f"{day_str} of {month_str} {year} {before_or_after}"

    def verify_date(self, date: Date) -> bool:
        return (
            date.month > 0 and date.month <= len(self._months) and
            date.day > 0 and date.day <= self._months[date.month - 1]["days"]
        )

    @property
    def num_days_of_year(self):
        return sum(month["days"] for month in self._months)

    def _get_month_num(self, month_name: str) -> int:
        for num, month in enumerate(self._months, 1):
            if month["name"] == month_name:
                return num
        raise Exception(f"Month {month_name} not found in calendar")

    def _day_of_year(self, date: Date) -> int:
        return date.day + sum(month["days"] for month in self._months[: date.month])

    def day_of_year(self, date: Date) -> int:
        if not self.verify_date(date): raise DateError(date)
        return self._day_of_year(date)

    def _remainder_of_month(self, date: Date) -> int:
        return self._months[date.month]["days"] - date.day

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
        return self._add_days(date, days)

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
