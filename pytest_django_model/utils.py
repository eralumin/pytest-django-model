# coding: utf-8

import os

import pytest
from django import get_version
from django.db.models import Field
from packaging import version

DJANGO_VERSION = get_version()

DEBUG = True if os.environ.get("DEBUG", None) else False


# DJANGO UTILS
##############
def get_django_all_models():
    if version.parse(DJANGO_VERSION) < version.parse("1.7.0"):
        from django.db.models.loading import cache

        all_models = cache.app_models
    else:
        from django.apps import apps

        all_models = apps.all_models

    return all_models


django_all_models = get_django_all_models()


def delete_django_model(app, model):
    try:
        del django_all_models[app][model.lower()]
    except KeyError:
        pass


def get_model_fields(model):
    if version.parse(DJANGO_VERSION) < version.parse("1.8.0"):
        fields = model._meta.fields + model._meta.local_many_to_many
    else:
        fields = [
            field for field in model._meta.get_fields() if isinstance(field, Field)
        ]

    return fields


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
