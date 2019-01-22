# coding: utf-8

import os

from .file import FILE
from .objects import AttributeObject
from .utils import a_or_an


def pytest_assertrepr_compare(op, left, right):
    assert_msg = lambda x: f"assert {left.value} == {right.value}\n" + x
    value_str = lambda x, y="": f" {x}." if len(str(x)) < 80 else f"{y}\n    {x}"

    if all(isinstance(obj, AttributeObject) for obj in [left, right]) and op == "==":
        msg = None
        if left.value is NotImplemented:
            msg = assert_msg(
                f"{left.breadcrumb} doesn't exist, the expected value is:\n"
                f"  - {right.cls}:{value_str(right.value)}"
            )
        elif left.cls != right.cls:
            msg = assert_msg(
                f"{left.breadcrumb} and {right.breadcrumb} are not the same type:\n"
                f"  - {left.breadcrumb} is {a_or_an(left.cls.__name__)} {left.cls}.\n"
                f"  - {right.breadcrumb} is {a_or_an(right.cls.__name__)} {right.cls}."
            )
        elif left.value != right.value:
            msg = assert_msg(
                f"{left.breadcrumb} and {right.breadcrumb} don't have the same value.\n"
                f"  - {left.breadcrumb} value is{value_str(left.value, ':')}\n"
                f"  - {right.breadcrumb} value is{value_str(right.value, ':')}"
            )

        return [msg] if msg else None


def pytest_sessionfinish(session, exitstatus):
    if os.path.isfile(FILE):
        os.remove(FILE)
