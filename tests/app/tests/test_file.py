# coding: utf-8

import os
import re
import sys

import pytest
from hypothesis import assume
from hypothesis import strategies as st
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    consumes,
    initialize,
    rule,
)

from pytest_django_models.file import FILE, FILE_HEADER, MODULE, FileGenerator
from pytest_django_models.objects import get_model_object

from .factories import (
    default_meta,
    fake_class_name,
    fake_constants,
    fake_fields_data,
)
from .utils import hasattrs, models_running, get_django_model


class StatefulTestFileGenerator(RuleBasedStateMachine):
    model_object = Bundle("model_object")

    name = Bundle("name")
    constants = Bundle("constants")
    fields = Bundle("fields")
    meta = Bundle("meta")

    @initialize()
    def remove_generated_file(self):
        if os.path.isfile(FILE):
            os.remove(FILE)

    @rule(target=name, name=fake_class_name())
    def add_name(self, name):
        assume(name.lower() not in models_running())
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

    @rule(
        target=model_object,
        name=consumes(name),
        constants=constants,
        fields=fields,
        meta=meta,
    )
    def add_model_object(self, name, constants, fields, meta):
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
        else:
            return model_object

    @rule(original=consumes(model_object), tester=consumes(model_object))
    def assert_file_generator(self, original, tester):
        initial_file = []
        if os.path.isfile(FILE):
            with open(FILE, "r") as f:
                initial_file = f.read().splitlines()

        file_generator_instance = FileGenerator(original, tester)

        # Test File exists.
        assert os.path.isfile(FILE)
        with open(FILE, "r") as f:
            modified_file = f.read().splitlines()

        # Test File has Header.
        assert all(
            modified_file[index] == line
            for index, line in enumerate(FILE_HEADER.splitlines())
        )

        # Test initial data isn't modified.
        for line_number, line in enumerate(initial_file):
            assert line == modified_file[line_number]

        # Test names are corrects and attributes exists.
        appended_data = modified_file[len(initial_file) :]
        pattern = r"assert (?P<original>\S+) == (?P<tester>\S+)"
        for line in appended_data:
            finded = re.search(pattern, line)
            if finded:
                finded = {
                    model: {
                        "name": breadcrumb.split(".")[0],
                        "attr": ".".join(breadcrumb.split(".")[1:]),
                    }
                    for model, breadcrumb in finded.groupdict().items()
                }

                # Test names are corrects.
                assert finded["original"]["name"] == original._meta.name
                assert finded["tester"]["name"] == tester._meta.name

                # Test attributes compared are the same.
                assert finded["original"]["attr"] == finded["tester"]["attr"]

                # Test attributes exists.
                assert hasattrs(original, finded["original"]["attr"])
                assert hasattrs(tester, finded["tester"]["attr"])

        # Try retrieve generated functions.
        try:
            generated_functions = file_generator_instance.get_functions()
        except Exception as e:
            pytest.fail(e)

        # Test Module Import.
        try:
            module = sys.modules[MODULE]

            # Test Module has the Generated Class.
            assert hasattr(module, tester._meta.name)

            # Test Generated Class has the generated functions.
            generated_class = getattr(module, tester._meta.name)
            for generated_function in generated_functions.keys():
                assert hasattr(generated_class, generated_function)
        except KeyError as e:
            pytest.fail(e)


TestFileGenerator = StatefulTestFileGenerator.TestCase
