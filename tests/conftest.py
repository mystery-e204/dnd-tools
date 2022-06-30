from scripts.fantasy_calendar import Date

def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, Date) and isinstance(right, Date):
        return [
            "Comparing Date instances:",
            f"   failed: {left} {op} {right}"
        ]