# coding: utf-8

import os

import pytest
from django import get_version
from packaging import version

DJANGO_VERSION = get_version()

if version.parse(DJANGO_VERSION) < version.parse("1.7.0"):
    from django.db.models.loading import cache
    django_models = cache.app_models
else:
    from django.apps import apps
    django_models = apps.all_models


DEBUG = True if os.environ.get("DEBUG", None) else False


# DJANGO UTILS
##############
delete_django_model = lambda app, model: django_models[app].pop(model.lower(), None)


# PYTEST UTILS
##############
def pytest_exit(err):
    exception = err.__class__
    error_msg = str(err)

    if DEBUG:
        raise exception(error_msg)
    else:
        pytest.exit(f"{exception.__name__}: {error_msg}")


# STRING FORMAT UTILS
#####################
def is_dunder(attr):
    return True if attr.startswith("__") else False


def a_or_an(string):
    return "an" if any(string.startswith(char) for char in "aeiouy") else "a"
