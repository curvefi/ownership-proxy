import pytest
import boa
from hypothesis import given, strategies as st


@pytest.fixture(scope="module")
def cooldown_test_contract():
    source = """
# pragma version 0.4.3

from contracts.permissions import cooldown

initializes: cooldown

@external
def test_add_from_days(key: bytes32, duration_days: uint256, override: bool = False):
    cooldown.add_from_days(key, duration_days, override)

@external
@view
def get_cooldown(key: bytes32) -> (uint128, uint128):
    return cooldown.cooldowns[key].start, cooldown.cooldowns[key].duration
"""
    return boa.loads(source)


def test_add_from_days_basic(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')
    duration_days = 7  # 1 week

    cooldown_test_contract.test_add_from_days(key, duration_days)

    start, stored_duration = cooldown_test_contract.get_cooldown(key)
    assert start == boa.env.timestamp
    assert stored_duration == duration_days * 86400


def test_add_from_days_zero_reverts(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')

    with boa.reverts("duration must be positive"):
        cooldown_test_contract.test_add_from_days(key, 0)


def test_add_from_days_overflow_reverts(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')
    # This will overflow when multiplied by 86400
    duration_days = 2**128 // 86400 + 1

    with boa.reverts("duration too large"):
        cooldown_test_contract.test_add_from_days(key, duration_days)


def test_add_from_days_existing_without_override(cooldown_test_contract):
    key = boa.eval('keccak256("test_days_1")')

    cooldown_test_contract.test_add_from_days(key, 1)

    with boa.reverts("cooldown already exists"):
        cooldown_test_contract.test_add_from_days(key, 2)


def test_add_from_days_existing_with_override(cooldown_test_contract):
    key = boa.eval('keccak256("test_days_2")')

    cooldown_test_contract.test_add_from_days(key, 1)
    cooldown_test_contract.test_add_from_days(key, 3, True)

    start, stored_duration = cooldown_test_contract.get_cooldown(key)
    assert start == boa.env.timestamp
    assert stored_duration == 3 * 86400


def test_add_from_days_conversion_accuracy(cooldown_test_contract):
    test_cases = [1, 7, 14, 30, 365]  # 1 day, 1 week, 2 weeks, 1 month, 1 year

    for i, days in enumerate(test_cases):
        test_key = boa.eval(f'keccak256("days_test_{i}")')
        cooldown_test_contract.test_add_from_days(test_key, days)

        start, stored_duration = cooldown_test_contract.get_cooldown(test_key)
        assert start == boa.env.timestamp
        assert stored_duration == days * 86400


@given(
    days=st.integers(min_value=1, max_value=(2**128 - 1) // 86400),
    key=st.binary(min_size=32, max_size=32),
)
def test_add_from_days_fuzz_valid(cooldown_test_contract, days, key):
    cooldown_test_contract.test_add_from_days(key, days)

    start, stored_duration = cooldown_test_contract.get_cooldown(key)
    assert start == boa.env.timestamp
    assert stored_duration == days * 86400


def test_add_from_days_max_safe_value(cooldown_test_contract):
    key = boa.eval('keccak256("test_max_days")')
    max_safe_days = (2**128 - 1) // 86400

    cooldown_test_contract.test_add_from_days(key, max_safe_days)

    start, stored_duration = cooldown_test_contract.get_cooldown(key)
    assert start == boa.env.timestamp
    assert stored_duration == max_safe_days * 86400
