# coding: utf-8

from collections import Counter
from operator import attrgetter

from django.db.models import Model

from pytest_django_model.utils import django_all_models

from .conftest import APP_LABEL


# ASSERT UTILS
##############
def hasattrs(instance, attrs):
    try:
        attrgetter(attrs)(instance)
        return True
    except AttributeError:
        return False


def have_difference(*args):
    elements = Counter([element for arg in args for element in arg])

    return [element for element, count in elements.items() if count == 1]


def have_similarities(*args):
    elements = Counter([element for arg in args for element in arg])

    return [element for element, count in elements.items() if count > 1]


def model_exists(model):
    django_model = django_all_models[APP_LABEL].pop(model.lower(), None)

    return True if django_model else False


# CREATE OBJECTS UTILS
######################
class Kwargs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def get_meta_class(**kwargs):
    return type("Meta", (), kwargs)


def get_field(field_data):
    field_class, attrs = field_data["class"], field_data["attrs"]
    return field_class(**attrs)


def get_fields(fields_data):
    fields = dict()
    for field_name, field_data in fields_data.items():
        fields[field_name] = get_field(field_data)

    return fields


def get_django_model(name, constants, fields, meta, parents=None):
    fields = get_fields(fields)

    dct = {
        "__module__": APP_LABEL,
        "Meta": get_meta_class(**meta),
        **constants,
        **fields,
    }
    bases = parents if parents else (Model,)

    return type(name, bases, dct)
