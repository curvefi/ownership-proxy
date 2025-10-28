import pytest
import boa
from hypothesis import given
from boa.test import strategies as boa_st


@pytest.fixture(scope="module")
def interval():
    source = """
# pragma version 0.4.3

from contracts.permissions import interval

initializes: interval

@external
def add_singleton_interval(key: bytes32, _value: uint256, override: bool = False):
    interval.add_singleton(key, _value, override)

@external
@view
def check(key: bytes32, _value: uint256):
    interval.check(key, _value)

exports: interval.__interface__
"""
    return boa.loads(source)


def test_add_singleton_interval_basic(interval):
    key = b"test_singleton"
    value = 42

    interval.add_singleton_interval(key, value, False)

    # Check that the interval is set correctly
    interval.check(key, value)

    # Check that only the exact value passes
    with boa.reverts("value out of interval"):
        interval.check(key, value - 1)

    with boa.reverts("value out of interval"):
        interval.check(key, value + 1)


def test_add_singleton_interval_zero(interval):
    key = b"test_zero_singleton"

    interval.add_singleton_interval(key, 0, False)

    # Check that only 0 passes
    interval.check(key, 0)

    with boa.reverts("value out of interval"):
        interval.check(key, 1)


def test_add_singleton_interval_max_value(interval):
    key = b"test_max_singleton"
    max_value = 2**256 - 1

    interval.add_singleton_interval(key, max_value, False)

    # Check that only max value passes
    interval.check(key, max_value)

    with boa.reverts("value out of interval"):
        interval.check(key, max_value - 1)


def test_add_singleton_interval_existing_without_override(interval):
    key = b"test_existing_singleton"

    interval.add_singleton_interval(key, 100, False)

    # Try to add another singleton without override
    with boa.reverts("interval already exists"):
        interval.add_singleton_interval(key, 200, False)


def test_add_singleton_interval_existing_with_override(interval):
    key = b"test_override_singleton"

    interval.add_singleton_interval(key, 100, False)
    interval.check(key, 100)

    # Override with new value
    interval.add_singleton_interval(key, 200, True)

    # Old value should fail
    with boa.reverts("value out of interval"):
        interval.check(key, 100)

    # New value should pass
    interval.check(key, 200)


@given(value=boa_st.strategy("uint256"))
def test_add_singleton_interval_fuzz(interval, value):
    key = b"test_fuzz_singleton"

    interval.add_singleton_interval(key, value, True)

    # Exact value should pass
    interval.check(key, value)

    # Any other value should fail
    if value > 0:
        with boa.reverts("value out of interval"):
            interval.check(key, value - 1)

    if value < 2**256 - 1:
        with boa.reverts("value out of interval"):
            interval.check(key, value + 1)


def test_add_singleton_interval_multiple_keys(interval):
    # Test that different keys are isolated
    key1 = b"singleton1"
    key2 = b"singleton2"

    interval.add_singleton_interval(key1, 100, False)
    interval.add_singleton_interval(key2, 200, False)

    # Each key should only accept its own value
    interval.check(key1, 100)
    interval.check(key2, 200)

    with boa.reverts("value out of interval"):
        interval.check(key1, 200)

    with boa.reverts("value out of interval"):
        interval.check(key2, 100)
