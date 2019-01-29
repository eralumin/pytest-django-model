# coding: utf-8

import os

from .file import FILE


def assert_msg(left, right):
    """Return Custom Assertion Message if Objects are equals else return None.
    """
    get_msg = lambda x: f"assert {left.value} == {right.value}\n" + x
    value_str = lambda x, y="": f" {x}" if len(str(x)) < 80 else f"{y}\n    {x}"

    if left.value is NotImplemented:
        msg = get_msg(
            f"{left.breadcrumb} doesn't exist, the expected value is:\n"
            f"  - {right.cls.__name__}: {value_str(right.value)}"
        )
    elif left.cls != right.cls:
        msg = get_msg(
            f"{left.breadcrumb} and {right.breadcrumb} are not the same type:\n"
            f"  - {left.breadcrumb} is {a_or_an(left.cls.__name__)} {left.cls}\n"
            f"  - {right.breadcrumb} is {a_or_an(right.cls.__name__)} {right.cls}"
        )
    elif left.value != right.value:
        msg = get_msg(
            f"{left.breadcrumb} and {right.breadcrumb} don't have the same value.\n"
            f"  - {left.breadcrumb} value is{value_str(left.value, ':')}\n"
            f"  - {right.breadcrumb} value is{value_str(right.value, ':')}"
        )
    else:
        msg = None

    return msg


def pytest_sessionfinish(session, exitstatus):
    if os.path.isfile(FILE):
        os.remove(FILE)
