# coding: utf-8

import pytest
from hypothesis import assume
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, consumes, rule

from pytest_django_model.objects import (
    META_OPTIONS,
    AttributeObject,
    ModelGenerator,
    ModelObject,
    get_model_object,
)

from .factories import (
    TYPES,
    default_meta,
    fake_class_name,
    fake_constants,
    fake_fields_data,
    fake_parents,
    fake_word,
)
from .utils import get_django_model, have_difference, model_exists


class StatefulTestAttributeObject(RuleBasedStateMachine):
    attribute_object = Bundle("attribute_object")

    name = Bundle("name")
    value = Bundle("value")
    parents = Bundle("parents")

    @rule(target=name, name=fake_word())
    def add_name(self, name):
        return name

    @rule(target=value, value=st.one_of(st.just(NotImplemented), *TYPES))
    def add_value(self, value):
        return value

    @rule(target=parents, parents=fake_parents())
    def add_parents(self, parents):
        return parents

    @rule(target=attribute_object, name=name, value=value, parents=parents)
    def add_attribute_object(self, name, value, parents):
        try:
            attribute_object = AttributeObject(name=name, value=value, parents=parents)
        except Exception as e:
            pytest.fail(e)

        assert attribute_object.cls == value.__class__
        assert attribute_object.name == name
        assert attribute_object.value == value
        assert attribute_object.parents == attribute_object.get_parents(parents)
        assert attribute_object.breadcrumb == f"{attribute_object.parents}.{name}"

        # Test __str__
        assert str(attribute_object) == f"{name}"

        # Test __repr__
        assert (
            repr(attribute_object)
            == f"<{attribute_object.breadcrumb}: {value.__class__.__name__}({value})>"
        )

        return attribute_object

    @rule(first=attribute_object, second=attribute_object)
    def compare_attribute_objects(self, first, second):
        # Test __eq__
        assert first == first

        if first != second:
            assert first.value != second.value or first.cls != second.cls
        else:
            assert first.value == second.value and first.cls == second.cls


TestAttributeObject = StatefulTestAttributeObject.TestCase


class StatefulPytestDjangoModelObject(RuleBasedStateMachine):
    model_object = Bundle("model_object")

    name = Bundle("name")
    constants = Bundle("constants")
    fields = Bundle("fields")
    meta = Bundle("meta")

    @rule(target=name, name=fake_class_name())
    def add_name(self, name):
        return name

    @rule(target=constants, constants=fake_constants())
    def add_constants(self, constants):
        return constants

    @rule(target=fields, fields=fake_fields_data())
    def add_fields(self, fields):
        return fields

    @rule(target=meta, meta=default_meta())
    def add_meta(self, meta):
        return meta

    @rule(target=model_object, name=name, constants=constants, fields=fields, meta=meta)
    def add_model_object(self, name, constants, fields, meta):
        # Remove Duplicates Fields.
        for field in fields:
            constants.pop(field, None)

        try:
            model_object = ModelObject(
                name=name, constants=constants, fields=fields, meta=meta
            )
        except Exception as e:
            pytest.fail(e)

        # Test _meta
        assert model_object._meta.name == name
        assert all(
            isinstance(getattr(model_object._meta, attr), dict)
            for attr in ["constants", "fields", "meta"]
        )
        assert not have_difference(constants, model_object._meta.constants)
        assert not have_difference(fields, model_object._meta.fields)
        assert not have_difference(meta, model_object._meta.meta)

        # Test Constants
        for attr, value in constants.items():
            assert hasattr(model_object, attr)
            assert getattr(model_object, attr).cls == constants[attr].__class__
            assert getattr(model_object, attr).value == constants[attr]
            assert getattr(model_object, attr).parents == name

        # Test Fields
        for attr, value in fields.items():
            assert hasattr(model_object, attr)
            assert getattr(model_object, attr).cls == fields[attr]["class"]
            assert getattr(model_object, attr).value == fields[attr]["attrs"]
            assert getattr(model_object, attr).parents == name

        # Test Meta
        assert hasattr(model_object, "Meta")
        post_meta = getattr(model_object, "Meta")
        for attr, value in meta.items():
            assert hasattr(post_meta, attr)
            assert getattr(post_meta, attr).cls == meta[attr].__class__
            assert getattr(post_meta, attr).value == meta[attr]
            assert getattr(post_meta, attr).parents == f"{name}.Meta"

        # Test __str__
        assert str(model_object) == model_object._meta.name

        # Test __repr__
        join = lambda x: ", ".join(x)
        assert repr(model_object) == (
            f"<{model_object._meta.name}: "
            f"constants({join(model_object._meta.constants)}), "
            f"fields({join(model_object._meta.fields)}), "
            f"Meta({join(model_object._meta.meta)})>"
        )

        return model_object


PytestDjangoModelObject = StatefulPytestDjangoModelObject.TestCase


def test_model_generator__get_default_meta_options():
    meta = ModelGenerator.get_default_meta_options()

    assert len(meta) == len(META_OPTIONS)
    assert all(option in meta for option in META_OPTIONS)


class StatefulPytestDjangoModelGenerator(RuleBasedStateMachine):
    name = Bundle("name")
    constants = Bundle("constants")
    fields = Bundle("fields")
    meta = Bundle("meta")

    @rule(target=name, name=fake_class_name())
    def add_name(self, name):
        assume(not model_exists(name))

        return name

    @rule(target=constants, constants=fake_constants())
    def add_constants(self, constants):
        return constants

    @rule(target=fields, fields=fake_fields_data())
    def add_fields(self, fields):
        return fields

    @rule(target=meta, meta=default_meta())
    def add_meta(self, meta):
        return meta

    @rule(name=consumes(name), constants=constants, fields=fields, meta=meta)
    def test_model_generator(self, name, constants, fields, meta):
        # Remove Duplicates Fields.
        for field in fields:
            constants.pop(field, None)

        try:
            django_model = get_django_model(
                name=name, constants=constants, fields=fields, meta=meta
            )
            model_object = get_model_object(django_model)
        except Exception as e:
            pytest.fail(e)

        # Test Constants
        assert hasattr(model_object._meta, "constants")
        for constant_name, value in constants.items():
            constant_attribute_object = AttributeObject(
                name=constant_name, value=value, parents=name
            )
            assert constant_name in model_object._meta.constants
            assert hasattr(model_object, constant_name)
            assert getattr(model_object, constant_name) == constant_attribute_object

        # Test Fields
        assert hasattr(model_object._meta, "fields")
        for field_name, data in fields.items():
            # Prepare object to test.
            field_attrs = data["class"](**data["attrs"]).deconstruct()[3]
            field_attribute_object = AttributeObject(
                name=field_name, cls=data["class"], value=field_attrs, parents=name
            )
            assert field_name in model_object._meta.fields
            assert hasattr(model_object, field_name)
            assert getattr(model_object, field_name) == field_attribute_object

        # Test Meta
        assert hasattr(model_object, "Meta")
        assert hasattr(model_object._meta, "meta")
        for option_name, value in meta.items():
            meta_attribute_object = AttributeObject(
                name=option_name, value=value, parents=[name, "Meta"]
            )
            assert option_name in model_object._meta.meta
            assert hasattr(model_object.Meta, option_name)
            assert getattr(model_object.Meta, option_name) == meta_attribute_object


PytestDjangoModelGenerator = StatefulPytestDjangoModelGenerator.TestCase
