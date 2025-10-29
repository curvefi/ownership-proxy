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
def test_add(key: bytes32, duration: uint256):
    cooldown.add(key, duration)

@external
def test_check_and_reset(key: bytes32):
    cooldown.check_and_reset(key)

@external
@view
def get_cooldown(key: bytes32) -> (uint128, uint128):
    return cooldown.cooldowns[key].start, cooldown.cooldowns[key].duration
"""
    return boa.loads(source)


def test_check_and_reset_expired_cooldown(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')
    duration = 3600  # 1 hour

    # Add cooldown
    cooldown_test_contract.test_add(key, duration)
    initial_timestamp = boa.env.timestamp

    # Try to check before expiry - should revert
    with boa.reverts("cooldown not expired"):
        cooldown_test_contract.test_check_and_reset(key)

    # Advance time past cooldown
    boa.env.time_travel(seconds=duration)

    # Now check should succeed
    cooldown_test_contract.test_check_and_reset(key)

    # Verify cooldown was reset
    start, stored_duration = cooldown_test_contract.get_cooldown(key)
    assert start == boa.env.timestamp  # Reset to current time
    assert stored_duration == duration  # Duration remains the same


def test_check_and_reset_exactly_at_expiry(cooldown_test_contract):
    key = boa.eval('keccak256("test_exact")')
    duration = 7200  # 2 hours

    cooldown_test_contract.test_add(key, duration)

    # Advance exactly to expiry
    boa.env.time_travel(seconds=duration)

    # Should succeed at exact expiry time
    cooldown_test_contract.test_check_and_reset(key)

    start, stored_duration = cooldown_test_contract.get_cooldown(key)
    assert start == boa.env.timestamp
    assert stored_duration == duration


def test_check_and_reset_one_second_before_expiry(cooldown_test_contract):
    key = boa.eval('keccak256("test_before")')
    duration = 3600

    cooldown_test_contract.test_add(key, duration)

    # Advance to one second before expiry
    boa.env.time_travel(seconds=duration - 1)

    # Should still revert
    with boa.reverts("cooldown not expired"):
        cooldown_test_contract.test_check_and_reset(key)


def test_check_and_reset_nonexistent_cooldown(cooldown_test_contract):
    key = boa.eval('keccak256("nonexistent")')

    # Check on non-existent cooldown should revert immediately
    # because start + duration = 0 + 0 = 0, and block.timestamp >= 0 is always true
    cooldown_test_contract.test_check_and_reset(key)

    # Verify it was set with current timestamp
    start, duration = cooldown_test_contract.get_cooldown(key)
    assert start == boa.env.timestamp
    assert duration == 0


def test_check_and_reset_multiple_times(cooldown_test_contract):
    key = boa.eval('keccak256("test_multiple")')
    duration = 1800  # 30 minutes

    cooldown_test_contract.test_add(key, duration)
    timestamps = []

    # Check and reset multiple times
    for i in range(3):
        boa.env.time_travel(seconds=duration)
        cooldown_test_contract.test_check_and_reset(key)

        start, stored_duration = cooldown_test_contract.get_cooldown(key)
        timestamps.append(start)
        assert start == boa.env.timestamp
        assert stored_duration == duration

        # Try immediate check - should fail
        with boa.reverts("cooldown not expired"):
            cooldown_test_contract.test_check_and_reset(key)

    # Verify timestamps are increasing
    for i in range(1, len(timestamps)):
        assert timestamps[i] > timestamps[i - 1]


def test_check_and_reset_long_cooldown(cooldown_test_contract):
    key = boa.eval('keccak256("test_long")')
    duration = 30 * 86400  # 30 days

    cooldown_test_contract.test_add(key, duration)

    # Advance time significantly past cooldown
    boa.env.time_travel(seconds=duration * 2)

    cooldown_test_contract.test_check_and_reset(key)

    start, stored_duration = cooldown_test_contract.get_cooldown(key)
    assert start == boa.env.timestamp
    assert stored_duration == duration


@given(
    duration=st.integers(min_value=1, max_value=86400 * 365),  # Up to 1 year
    extra_time=st.integers(min_value=0, max_value=86400),  # Extra time past expiry
)
def test_check_and_reset_fuzz(cooldown_test_contract, duration, extra_time):
    key = boa.eval(f'keccak256("fuzz_{duration}_{extra_time}")')

    cooldown_test_contract.test_add(key, duration)

    # Advance past cooldown
    boa.env.time_travel(seconds=duration + extra_time)

    cooldown_test_contract.test_check_and_reset(key)

    start, stored_duration = cooldown_test_contract.get_cooldown(key)
    assert start == boa.env.timestamp
    assert stored_duration == duration
