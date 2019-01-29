# coding: utf-8

import pytest
from hypothesis import assume
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule

from pytest_django_model.objects import AttributeObject
from pytest_django_model.plugin import assert_msg

from .factories import TYPES, fake_parents, fake_word


class StatefulTestAssertMsg(RuleBasedStateMachine):
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
    def test_assert_msg(self, left, right):
        assume(left != right)

        try:
            msg = assert_msg(left, right)
        except Exception as e:
            pytest.fail(e)
        else:
            msg_start = f"assert {left.value} == {right.value}\n"
            if left.value is NotImplemented:
                assert msg.startswith(
                    msg_start
                    + f"{left.breadcrumb} doesn't exist, "
                    + "the expected value is:\n"
                )
            elif left.cls != right.cls:
                assert msg.startswith(
                    msg_start
                    + f"{left.breadcrumb} and {right.breadcrumb} "
                    + "are not the same type:\n"
                )
            elif left.value != right.value:
                assert msg.startswith(
                    msg_start
                    + f"{left.breadcrumb} and {right.breadcrumb} "
                    + "don't have the same value.\n"
                )
            else:
                assert msg is None

TestAssertMsg = StatefulTestAssertMsg.TestCase
