# coding: utf-8

from itertools import chain

import pytest
from django.db.models import CharField
from hypothesis import assume
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, consumes, rule

from pytest_django_models.core import (
    InvalidModelError,
    ModelNotFoundError,
    TestModel,
    get_invalid_model_msg,
)
from pytest_django_models.objects import get_model_object

from .factories import (
    BASIC_TYPES,
    default_meta,
    fake_attr_name,
    fake_class_name,
    fake_constants,
    fake_fields_data,
)
from .utils import (
    Kwargs,
    get_django_model,
    get_fields,
    get_meta_class,
    have_similarities,
    models_running,
)


class StatefulTestTestModel(RuleBasedStateMachine):
    # Basic Components
    ##################
    name = Bundle("name")

    @rule(target=name, name=fake_class_name())
    def add_name(self, name):
        assume(name.lower() not in models_running())

        return name

    # Intermediate Components
    #########################
    model_data = Bundle("model_data")
    parent = Bundle("parent")

    @rule(
        target=model_data,
        name=consumes(name),
        constants=fake_constants(),
        fields=fake_fields_data(),
        meta=default_meta(),
    )
    def add_model(self, name, constants, fields, meta):
        # Remove Duplicates Fields
        for field in fields:
            constants.pop(field, None)

        return Kwargs(name=name, constants=constants, fields=fields, meta=meta)

    @rule(
        target=parent,
        name=consumes(name),
        constants=fake_constants(),
        fields=fake_fields_data(min_size=1),
        meta=default_meta(),
        pk_name=fake_attr_name(),
    )
    def add_parent(self, name, constants, fields, meta, pk_name):
        try:
            pk = {
                pk_name: {
                    "class": CharField,
                    "attrs": {"primary_key": True, "max_length": 256},
                }
            }
            parent = get_django_model(
                name=name, constants=constants, fields={**pk, **fields}, meta=meta
            )
        except Exception as e:
            pytest.fail(e)
        else:
            parent.fields = [
                field.name
                for field in chain(
                    parent._meta.local_fields, parent._meta.local_many_to_many
                )
            ]

            return parent

    # TestModel Components
    ######################
    data = Bundle("data")

    @rule(
        target=data,
        original=consumes(model_data),
        tester=consumes(model_data),
        parents=st.lists(elements=parent, max_size=3, unique=True).filter(
            lambda parents: not have_similarities(
                *[parent.fields for parent in parents]
            )
        ),
    )
    def add_test_model_data(self, original, tester, parents):
        # Remove Duplicates Fields with Parents.
        parents_fields = [field for parent in parents for field in parent.fields]
        for field in parents_fields:
            original.fields.pop(field, None)
            tester.fields.pop(field, None)

        # Prepare Original Objects.
        try:
            original_django_model = get_django_model(
                name=original.name,
                constants=original.constants,
                fields=original.fields,
                meta=original.meta,
                parents=tuple(parents),
            )
            original_model_object = get_model_object(original_django_model)
            original = Kwargs(
                data=original,
                django_model=original_django_model,
                model_object=original_model_object,
            )
        except Exception as e:
            pytest.fail(e)

        # Prepare Test Model dct.
        dct = {
            **tester.constants,
            **get_fields(tester.fields),
            "Meta": get_meta_class(**tester.meta),
        }

        name = tester.name
        dct["Meta"].model = original.django_model
        dct["Meta"].parents = parents

        return Kwargs(
            original=original, tester=tester, parents=parents, name=name, dct=dct
        )

    # Tests
    #######
    dirty_fields = Bundle("dirty_fields")

    @rule(
        target=dirty_fields,
        cls_name=consumes(name),
        fields=fake_fields_data(dirty=True, min_size=1),
    )
    def add_dirty_fields(self, cls_name, fields):
        django_model = get_django_model(cls_name, constants={}, fields=fields, meta={})
        assume(django_model.check())

        return get_fields(fields)

    @rule(data=consumes(data))
    def assert_no_error(self, data):
        original, tester, parents = data.original, data.tester, data.parents
        name, bases, dct = data.tester.name, (), data.dct

        name = tester.name
        dct["Meta"].model = original.django_model
        dct["Meta"].parents = parents

        try:
            test_model = TestModel(name, bases, dct)
        except Exception as e:
            pytest.fail(e)

    @rule(data=consumes(data))
    def assert_no_meta(self, data):
        original, tester, parents = data.original, data.tester, data.parents
        name, bases, dct = data.tester.name, (), data.dct

        dct.pop("Meta")

        error_msg = f"{name} must have a 'Meta' inner class with 'model' attribute."
        with pytest.raises(ModelNotFoundError, match=error_msg):
            TestModel(name, bases, dct)

    @rule(data=consumes(data), invalid_class_name=consumes(name))
    def assert_original_model_not_found(self, data, invalid_class_name):
        original, tester, parents = data.original, data.tester, data.parents
        name, bases, dct = data.tester.name, (), data.dct

        delattr(dct["Meta"], "model")

        error_msg = f"'Meta' inner class has not 'model' attribute."
        with pytest.raises(ModelNotFoundError, match=error_msg):
            TestModel(name, bases, dct)

    @rule(
        data=consumes(data),
        invalid_class_name=consumes(name),
        invalid_type=st.one_of(BASIC_TYPES),
        isclass=st.booleans(),
    )
    def assert_original_is_invalid_model(
        self, data, invalid_class_name, invalid_type, isclass
    ):
        original, tester, parents = data.original, data.tester, data.parents
        name, bases, dct = data.tester.name, (), data.dct

        invalid_class = type(invalid_class_name, (), {}) if isclass else invalid_type
        dct["Meta"].model = invalid_class

        error_msg = get_invalid_model_msg(invalid_class)
        with pytest.raises(InvalidModelError, match=error_msg):
            TestModel(name, bases, dct)

    @rule(
        data=consumes(data),
        invalid_class_name=consumes(name),
        isiterable=st.booleans(),
        invalid_type=st.one_of(BASIC_TYPES),
        isclass=st.booleans(),
    )
    def assert_parents_invalid_model(
        self, data, invalid_class_name, invalid_type, isclass, isiterable
    ):
        original, tester, parents = data.original, data.tester, data.parents
        name, bases, dct = data.tester.name, (), data.dct

        invalid_class = type(invalid_class_name, (), {}) if isclass else invalid_type
        error_msg = get_invalid_model_msg(invalid_class)

        if isiterable:
            dct["Meta"].parents.append(invalid_class)
            error_msg = f"'parents' contains invalid model: {error_msg}"
        else:
            dct["Meta"].parents = invalid_class
            error_msg = f"'parents': {error_msg}"

        with pytest.raises(InvalidModelError, match=error_msg):
            TestModel(name, bases, dct)

    @rule(data=consumes(data), dirty_fields=dirty_fields)
    def assert_is_invalid_model(self, data, dirty_fields):
        original, tester, parents = data.original, data.tester, data.parents
        name, bases, dct = data.tester.name, (), data.dct

        # Assume any Dirty Field in Parents Fields.
        parents_fields = [field for parent in parents for field in parent.fields]
        assume(not have_similarities(dirty_fields, parents_fields))

        dct = {**dct, **dirty_fields}

        error_msg = (
            fr"^The {name} Model get the following errors during validation:(.|\s)+"
        )
        with pytest.raises(InvalidModelError, match=error_msg):
            TestModel(name, bases, dct)


TestTestModel = StatefulTestTestModel.TestCase
