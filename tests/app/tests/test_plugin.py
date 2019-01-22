# coding: utf-8

import pytest
from hypothesis import assume
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule

from pytest_django_model.objects import AttributeObject
from pytest_django_model.plugin import pytest_assertrepr_compare

from .factories import OPERATORS, TYPES, fake_parents, fake_word


class StatefulTestPytestAssertReprCompare(RuleBasedStateMachine):
    attribute_object = Bundle("attribute_object")

    @rule(
        target=attribute_object,
        name=fake_word(),
        value=st.one_of(st.just(NotImplemented), *TYPES),
        parents=fake_parents(),
    )
    def add_attribute_object(self, name, value, parents):
        try:
            attribute_object = AttributeObject(name=name, value=value, parents=parents)
        except Exception as e:
            pytest.fail(e)

        return attribute_object

    @rule(
        left=attribute_object,
        right=attribute_object.filter(lambda x: x.value != NotImplemented),
    )
    def assert_msg(self, left, right):
        assume(left != right)

        try:
            msgs = pytest_assertrepr_compare("==", left, right)
        except Exception as e:
            pytest.fail(e)
        else:
            assert len(msgs) == 1
            assert isinstance(msgs, list)

            msg = msgs[0]
            assert isinstance(msg, str)

            assert_msg = f"assert {left.value} == {right.value}\n"
            if left.value is NotImplemented:
                assert msg.startswith(
                    assert_msg
                    + f"{left.breadcrumb} doesn't exist, "
                    + "the expected value is:\n"
                )
            elif left.cls != right.cls:
                assert msg.startswith(
                    assert_msg
                    + f"{left.breadcrumb} and {right.breadcrumb} "
                    + "are not the same type:\n"
                )
            elif left.value != right.value:
                assert msg.startswith(
                    assert_msg
                    + f"{left.breadcrumb} and {right.breadcrumb} "
                    + "don't have the same value.\n"
                )

    @rule(
        left=attribute_object.filter(lambda x: x.value != NotImplemented),
        right=attribute_object.filter(lambda x: x.value != NotImplemented),
    )
    def assert_equals_no_msg(self, left, right):
        assume(left == right)

        try:
            msgs = pytest_assertrepr_compare("==", left, right)
        except Exception as e:
            pytest.fail(e)
        else:
            assert msgs is None

    @rule(
        op=st.one_of(*OPERATORS).filter(lambda x: x != "=="),
        left=st.one_of(attribute_object, *TYPES),
        right=st.one_of(attribute_object, *TYPES),
    )
    def assert_no_msg(self, op, left, right):
        assume(any(not isinstance(obj, AttributeObject) for obj in [left, right]))

        try:
            msgs = pytest_assertrepr_compare(op, left, right)
        except Exception as e:
            pytest.fail(e)
        else:
            assert msgs is None


TestPytestAssertReprCompare = StatefulTestPytestAssertReprCompare.TestCase
