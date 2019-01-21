# coding: utf-8

import os
import pytest

DEBUG = True if os.environ.get("DEBUG", None) else False

def pytest_exit(err):
    exception = err.__class__
    error_msg = str(err)

    if DEBUG:
        raise exception(error_msg)
    else:
        pytest.exit(f"{exception.__name__}: {error_msg}")


def is_dunder(attr):
    return True if attr.startswith("__") else False

def a_or_an(string):
    return "an" if any(string.startswith(char) for char in "aeiouy") else "a"