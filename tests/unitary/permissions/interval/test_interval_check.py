import pytest
import boa
from hypothesis import given, strategies as st


@pytest.fixture(scope="module")
def interval_test_contract():
    source = """
# pragma version 0.4.3

from contracts.permissions import interval

initializes: interval

@external
def test_add(key: bytes32, lb: uint256, ub: uint256, override: bool = False):
    interval.add(key, lb, ub, override)

@external
def test_check(key: bytes32, val: uint256):
    interval.check(key, val)
"""
    return boa.loads(source)


def test_check_within_range_passes(interval_test_contract):
    key = boa.eval('keccak256("test_range")')
    lb = 100
    ub = 200

    # Add range
    interval_test_contract.test_add(key, lb, ub)

    # Check values within range
    interval_test_contract.test_check(key, 100)  # Lower bound
    interval_test_contract.test_check(key, 150)  # Middle
    interval_test_contract.test_check(key, 200)  # Upper bound


def test_check_outside_range_reverts(interval_test_contract):
    key = boa.eval('keccak256("test_outside")')
    lb = 100
    ub = 200

    # Add range
    interval_test_contract.test_add(key, lb, ub)

    # Check values outside range
    with boa.reverts("value out of interval"):
        interval_test_contract.test_check(key, 99)  # Below lower bound

    with boa.reverts("value out of interval"):
        interval_test_contract.test_check(key, 201)  # Above upper bound


def test_check_nonexistent_range_reverts(interval_test_contract):
    key = boa.eval('keccak256("test_nonexistent")')

    with boa.reverts("interval does not exist"):
        interval_test_contract.test_check(key, 150)


def test_check_zero_range(interval_test_contract):
    key = boa.eval('keccak256("test_zero")')

    # Add singleton range [0, 0]
    interval_test_contract.test_add(key, 0, 0)

    # Only 0 should pass
    interval_test_contract.test_check(key, 0)

    with boa.reverts("value out of interval"):
        interval_test_contract.test_check(key, 1)


def test_check_max_range(interval_test_contract):
    key = boa.eval('keccak256("test_max")')
    max_uint = 2**256 - 1

    # Add full range [0, max]
    interval_test_contract.test_add(key, 0, max_uint)

    # Any value should pass
    interval_test_contract.test_check(key, 0)
    interval_test_contract.test_check(key, max_uint // 2)
    interval_test_contract.test_check(key, max_uint)


def test_check_inverted_range(interval_test_contract):
    key = boa.eval('keccak256("test_inverted")')

    # Trying to add inverted range [200, 100] should revert
    with boa.reverts("inverted range: lb > ub"):
        interval_test_contract.test_add(key, 200, 100)


@given(
    lb=st.integers(min_value=0, max_value=1000),
    ub=st.integers(min_value=0, max_value=1000),
    value=st.integers(min_value=0, max_value=1000),
)
def test_check_fuzz(interval_test_contract, lb, ub, value):
    key = boa.eval('keccak256("test_fuzz")')

    # Skip inverted ranges (lb > ub) since they're not allowed
    if lb > ub:
        with boa.reverts("inverted range: lb > ub"):
            interval_test_contract.test_add(key, lb, ub, True)
        return

    # Add range
    interval_test_contract.test_add(key, lb, ub, True)

    # Check if value is in range
    if lb <= value <= ub:
        # Should pass
        interval_test_contract.test_check(key, value)
    else:
        # Should revert
        with boa.reverts("value out of interval"):
            interval_test_contract.test_check(key, value)
