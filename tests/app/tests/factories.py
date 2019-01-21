# coding: utf-8

import keyword

import hypothesis.strategies as st
from django.db import models
from faker import Faker
from hypothesis.strategies import composite

from pytest_django_models.objects import ModelGenerator


APP_LABEL = "app"

fake = Faker()


# TYPES FACTORIES
#################
def fake_word():
    blacklist_base = [
        "constant",
        "field",
        "id",
        "meta",
        "name",
        "parent",
        "test",
        "value",
    ] + keyword.kwlist
    blacklist_plurals = [f"{word}s" for word in blacklist_base]
    blacklist = [word.lower() for word in [*blacklist_base, *blacklist_plurals]]

    return st.builds(fake.word).filter(lambda x: not x.lower() in blacklist)


def fake_text():
    return st.builds(fake.text, max_nb_chars=st.integers(min_value=5, max_value=100))


BASIC_TYPES = [
    fake_text(),
    st.integers(),
    st.floats(allow_nan=False),
    st.booleans(),
    st.none(),
]

DICTS = st.dictionaries(keys=fake_word(), values=st.one_of(BASIC_TYPES), max_size=5)
LISTS = st.lists(elements=st.one_of(BASIC_TYPES), max_size=5)
TUPLES = st.tuples(LISTS)

DATA_STRUCTURE_TYPES = [DICTS, LISTS, TUPLES]

COMPLEX_DICTS = st.dictionaries(
    keys=fake_word(), values=st.one_of(DATA_STRUCTURE_TYPES), max_size=5
)
COMPLEX_LISTS = st.lists(elements=st.one_of(DATA_STRUCTURE_TYPES), max_size=5)
COMPLEX_TUPLES = st.tuples(COMPLEX_LISTS)

COMPLEX_DATA_STRUCTURE_TYPES = [COMPLEX_DICTS, COMPLEX_LISTS, COMPLEX_TUPLES]

TYPES = [*BASIC_TYPES, *DATA_STRUCTURE_TYPES, *COMPLEX_DATA_STRUCTURE_TYPES]

OPERATORS = [st.just(op) for op in ["==", "!=", ">", "<", ">=", "<="]]

# OBJECTS FACTORIES
###################
@composite
def fake_class_name(draw):
    words = draw(st.lists(elements=fake_word(), min_size=1, max_size=3))

    return "".join([word.title() for word in words])


@composite
def fake_attr_name(draw):
    words = draw(st.lists(elements=fake_word(), min_size=1, max_size=3))

    return "_".join([word for word in words])


def fake_class(**kwargs):
    return type(fake_class_name(), (), kwargs)


def fake_parents():
    parents_list = st.lists(elements=fake_class_name(), min_size=1, max_size=2)
    parents_str = fake_class_name()

    return st.one_of(parents_list, parents_str)


def fake_constant():
    return st.one_of(DATA_STRUCTURE_TYPES)


def fake_constants():
    return st.dictionaries(keys=fake_attr_name(), values=fake_constant(), max_size=5)

@composite
def fake_field_data(draw, dirty=False):
    if dirty:
        dirty = lambda x: not x
    else:
        dirty = lambda x: x

    # Get Field
    field = draw(st.one_of([st.just(field) for field in FIELDS]))

    # Get Attributes
    field_attrs = dict()
    for attr, settings in FIELD_ATTRS.items():
        if dirty(field in settings.get("excluded", [])):
            pass
        elif dirty(field in settings.get("required", [])):
            field_attrs[attr] = settings["value"]
        elif fake.pybool():
            field_attrs[attr] = settings["value"]

    field_attrs = {attr: draw(value) for attr, value in field_attrs.items()}
    return {"class": field, "attrs": field_attrs}


def fake_fields_data(dirty=False, min_size=0):
    return st.dictionaries(keys=fake_attr_name(), values=fake_field_data(dirty), min_size=min_size, max_size=5)


@composite
def fake_field(draw):
    field, attrs = draw(fake_field_data()).values()
    return field(**attrs)


def fake_fields():
    return st.dictionaries(keys=fake_attr_name(), values=fake_field(), max_size=5)


def default_meta():
    return st.builds(ModelGenerator.get_default_meta_options)


# MODEL FACTORIES
#################
# @composite
# def fake_rel_field(draw):
#     to_self = "self"
#     to_another_field = type(
#         fake_class_name(),
#         (models.Model,),
#         {"Meta": get_meta_class(), "__module__": APP_LABEL},
#     )

#     return draw(st.one_of(to_self, to_another_field))


BINARY_FIELDS = [models.BinaryField, models.FileField]
BOOL_FIELDS = [models.BooleanField, models.NullBooleanField]
CHAR_FIELDS = [models.CharField, models.EmailField, models.TextField, models.URLField]
NUMERIC_FIELDS = [models.IntegerField, models.SmallIntegerField, models.FloatField]
REL_FIELDS = []  # models.ForeignKey, models.ManyToManyField, models.OneToOneField]

FIELDS = [*BINARY_FIELDS, *BOOL_FIELDS, *CHAR_FIELDS, *NUMERIC_FIELDS, *REL_FIELDS]

FIELD_ATTRS = {
    "null": {"required": [*FIELDS], "excluded": [*CHAR_FIELDS], "value": st.just(True)},
    "blank": {"required": [*FIELDS], "value": st.just(True)},
    "db_column": {"value": fake_word()},
    "db_index": {"value": st.one_of(st.booleans(), st.none())},
    "db_tablespace": {"value": fake_word()},
    "editable": {"value": st.booleans()},
    "help_text": {"value": fake_text()},
    "max_length": {
        "excluded": [
            *BINARY_FIELDS,
            *BOOL_FIELDS,
            *NUMERIC_FIELDS,
            *REL_FIELDS,
            models.TextField,
        ],
        "required": [models.CharField, models.EmailField, models.URLField],
        "value": st.integers(min_value=0, max_value=255),
    },
    "unique": {"value": st.booleans()},
    "verbose_name": {"value": fake_word()},
    # # REL FIELDS ATTRS
    # "to": {
    #     "excluded": [*BINARY_FIELDS, *BOOL_FIELDS, *CHAR_FIELDS, *NUMERIC_FIELDS],
    #     "required": [*REL_FIELDS],
    #     "value": fake_rel_field(),
    # },
    # "on_delete": {
    #     "excluded": [*BINARY_FIELDS, *BOOL_FIELDS, *CHAR_FIELDS, *NUMERIC_FIELDS],
    #     "required": [*REL_FIELDS],
    #     "value": st.just(models.CASCADE),
    # },
}
