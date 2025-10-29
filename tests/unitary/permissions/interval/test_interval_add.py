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

exports: interval.__interface__
"""
    return boa.loads(source)


def test_add_basic_range(interval_test_contract):
    key = boa.eval('keccak256("test_range")')
    lb = 100
    ub = 200

    interval_test_contract.test_add(key, lb, ub)

    # Access public storage directly
    stored_lb, stored_ub = interval_test_contract.intervals(key)
    assert stored_lb == lb
    assert stored_ub == ub


def test_add_inverted_range(interval_test_contract):
    key = boa.eval('keccak256("inverted_range")')
    # Contract should reject inverted ranges where lb > ub

    with boa.reverts("inverted range: lb > ub"):
        interval_test_contract.test_add(key, 200, 100)


def test_add_existing_without_override_reverts(interval_test_contract):
    key = boa.eval('keccak256("existing_range")')

    interval_test_contract.test_add(key, 10, 20)

    with boa.reverts("interval already exists"):
        interval_test_contract.test_add(key, 30, 40)


def test_add_existing_with_override_succeeds(interval_test_contract):
    key = boa.eval('keccak256("override_range")')

    interval_test_contract.test_add(key, 10, 20)
    interval_test_contract.test_add(key, 30, 40, True)

    stored_lb, stored_ub = interval_test_contract.intervals(key)
    assert stored_lb == 30
    assert stored_ub == 40


def test_add_multiple_ranges(interval_test_contract):
    ranges = [
        (boa.eval('keccak256("range1")'), 0, 100),
        (boa.eval('keccak256("range2")'), 50, 150),
        (boa.eval('keccak256("range3")'), 1000, 2000),
    ]

    for key, lb, ub in ranges:
        interval_test_contract.test_add(key, lb, ub)

    for key, expected_lb, expected_ub in ranges:
        stored_lb, stored_ub = interval_test_contract.intervals(key)
        assert stored_lb == expected_lb
        assert stored_ub == expected_ub


@given(
    lb=st.integers(min_value=0, max_value=2**256 - 1),
    ub=st.integers(min_value=0, max_value=2**256 - 1),
    key=st.binary(min_size=32, max_size=32),
)
def test_add_fuzz_any_range(interval_test_contract, lb, ub, key):
    if lb > ub:
        # Test that inverted ranges are rejected
        with boa.reverts("inverted range: lb > ub"):
            interval_test_contract.test_add(key, lb, ub)
    else:
        # Test that valid ranges are accepted
        interval_test_contract.test_add(key, lb, ub)

        stored_lb, stored_ub = interval_test_contract.intervals(key)
        assert stored_lb == lb
        assert stored_ub == ub
