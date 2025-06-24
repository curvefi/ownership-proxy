import pytest
import boa
from hypothesis import given, settings
from boa.test.strategies import strategy


@pytest.fixture(scope="module")
def interval_contract():
    source_code = """
# pragma version 0.4.3

from contracts.permissions import interval

initializes: interval

@external
def test_add_singleton(key: bytes32, val: uint256, override: bool = True):
    interval.add_singleton(key, val, override)

@external
@view
def get_range(key: bytes32) -> (uint256, uint256):
    return interval.intervals[key].lb, interval.intervals[key].ub
"""
    return boa.loads(source_code)


def test_add_singleton_interval_basic(interval_contract):
    key = b"test_singleton"
    value = 42

    interval_contract.test_add_singleton(key, value)

    lb, ub = interval_contract.get_range(key)
    assert lb == value
    assert ub == value


def test_add_singleton_interval_zero(interval_contract):
    key = b"test_zero"
    value = 0
    
    interval_contract.test_add_singleton(key, value)
    
    lb, ub = interval_contract.get_range(key)
    assert lb == 0
    assert ub == 0


def test_add_singleton_interval_max_value(interval_contract):
    key = b"test_max"
    value = 2**256 - 1
    
    interval_contract.test_add_singleton(key, value)
    
    lb, ub = interval_contract.get_range(key)
    assert lb == value
    assert ub == value


def test_add_singleton_interval_existing_without_override(interval_contract):
    key = b"test_existing"
    value1 = 100
    value2 = 200
    
    interval_contract.test_add_singleton(key, value1)
    
    with boa.reverts("interval already exists"):
        interval_contract.test_add_singleton(key, value2, False)


def test_add_singleton_interval_existing_with_override(interval_contract):
    key = b"test_override"
    value1 = 100
    value2 = 200
    
    interval_contract.test_add_singleton(key, value1)
    interval_contract.test_add_singleton(key, value2, True)
    
    lb, ub = interval_contract.get_range(key)
    assert lb == value2
    assert ub == value2


@given(value=strategy("uint256"))
@settings(max_examples=20)
def test_add_singleton_interval_fuzz(interval_contract, value):
    key = boa.env.generate_address().encode()[:32]
    
    interval_contract.test_add_singleton(key, value)
    
    lb, ub = interval_contract.get_range(key)
    assert lb == value
    assert ub == value


def test_add_singleton_interval_multiple_keys(interval_contract):
    keys = [b"key1", b"key2", b"key3"]
    values = [10, 20, 30]
    
    for key, value in zip(keys, values):
        interval_contract.test_add_singleton(key, value)
    
    for key, expected_value in zip(keys, values):
        lb, ub = interval_contract.get_range(key)
        assert lb == expected_value
        assert ub == expected_value