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
def test_add_from_hours(key: bytes32, duration_hours: uint256, override: bool = False):
    cooldown.add_from_hours(key, duration_hours, override)

@external
@view
def cooldowns(key: bytes32) -> (uint128, uint128):
    return cooldown.cooldowns[key].start, cooldown.cooldowns[key].duration

@external
@view
def get_cooldown(key: bytes32) -> (uint128, uint128):
    return cooldown.cooldowns[key].start, cooldown.cooldowns[key].duration
"""
    return boa.loads(source)


def test_add_from_hours_basic(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')
    duration_hours = 2

    cooldown_test_contract.test_add_from_hours(key, duration_hours)

    start, stored_duration = cooldown_test_contract.cooldowns(key)
    assert start == boa.env.timestamp
    assert stored_duration == duration_hours * 3600


def test_add_from_hours_zero_reverts(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')

    with boa.reverts("duration must be positive"):
        cooldown_test_contract.test_add_from_hours(key, 0)


def test_add_from_hours_overflow_reverts(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')
    # This will overflow when multiplied by 3600
    duration_hours = 2**128 // 3600 + 1

    with boa.reverts("duration too large"):
        cooldown_test_contract.test_add_from_hours(key, duration_hours)


def test_add_from_hours_existing_without_override(cooldown_test_contract):
    key = boa.eval('keccak256("test_hours_1")')

    cooldown_test_contract.test_add_from_hours(key, 1)

    with boa.reverts("cooldown already exists"):
        cooldown_test_contract.test_add_from_hours(key, 2)


def test_add_from_hours_existing_with_override(cooldown_test_contract):
    key = boa.eval('keccak256("test_hours_2")')

    cooldown_test_contract.test_add_from_hours(key, 1)
    cooldown_test_contract.test_add_from_hours(key, 3, True)

    start, stored_duration = cooldown_test_contract.cooldowns(key)
    assert start == boa.env.timestamp
    assert stored_duration == 3 * 3600


def test_add_from_hours_conversion_accuracy(cooldown_test_contract):
    test_cases = [1, 24, 48, 168]  # 1 hour, 1 day, 2 days, 1 week

    for i, hours in enumerate(test_cases):
        test_key = boa.eval(f'keccak256("hours_test_{i}")')
        cooldown_test_contract.test_add_from_hours(test_key, hours)

        start, stored_duration = cooldown_test_contract.get_cooldown(test_key)
        assert start == boa.env.timestamp
        assert stored_duration == hours * 3600


@given(
    hours=st.integers(min_value=1, max_value=(2**128 - 1) // 3600),
    key=st.binary(min_size=32, max_size=32),
)
def test_add_from_hours_fuzz_valid(cooldown_test_contract, hours, key):
    cooldown_test_contract.test_add_from_hours(key, hours)

    start, stored_duration = cooldown_test_contract.cooldowns(key)
    assert start == boa.env.timestamp
    assert stored_duration == hours * 3600


def test_add_from_hours_max_safe_value(cooldown_test_contract):
    key = boa.eval('keccak256("test_max_hours")')
    max_safe_hours = (2**128 - 1) // 3600

    cooldown_test_contract.test_add_from_hours(key, max_safe_hours)

    start, stored_duration = cooldown_test_contract.cooldowns(key)
    assert start == boa.env.timestamp
    assert stored_duration == max_safe_hours * 3600
