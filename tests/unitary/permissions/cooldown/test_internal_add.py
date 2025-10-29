import pytest
import boa
from hypothesis import given, strategies as st


def get_cooldown(contract, key_str):
    """Helper to get cooldown storage values using eval"""
    start = contract.eval(f'cooldown.cooldowns[keccak256("{key_str}")].start')
    duration = contract.eval(f'cooldown.cooldowns[keccak256("{key_str}")].duration')
    return start, duration


@pytest.fixture(scope="module")
def cooldown_test_contract():
    source = """
# pragma version 0.4.3

from contracts.permissions import cooldown

initializes: cooldown

@external
def test_add(key: bytes32, duration: uint256, override: bool = False):
    cooldown.add(key, duration, override)

@external
@view
def get_cooldown_raw(key: bytes32) -> (uint128, uint128):
    return cooldown.cooldowns[key].start, cooldown.cooldowns[key].duration
"""
    return boa.loads(source)


def test_add_basic(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')
    duration = 3600  # 1 hour

    cooldown_test_contract.test_add(key, duration)

    start, stored_duration = get_cooldown(cooldown_test_contract, "test_cooldown")
    assert start == boa.env.timestamp
    assert stored_duration == duration


def test_add_zero_duration_reverts(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')

    with boa.reverts("duration must be positive"):
        cooldown_test_contract.test_add(key, 0)


def test_add_duration_too_large_reverts(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')

    with boa.reverts("duration too large"):
        cooldown_test_contract.test_add(key, 2**128)


def test_add_existing_without_override_reverts(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')
    duration = 3600

    cooldown_test_contract.test_add(key, duration)

    with boa.reverts("cooldown already exists"):
        cooldown_test_contract.test_add(key, duration * 2)


def test_add_existing_with_override_succeeds(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')
    duration1 = 3600
    duration2 = 7200

    cooldown_test_contract.test_add(key, duration1)
    cooldown_test_contract.test_add(key, duration2, True)

    start, stored_duration = get_cooldown(cooldown_test_contract, "test_cooldown")
    assert start == boa.env.timestamp
    assert stored_duration == duration2


def test_add_multiple_keys(cooldown_test_contract):
    key_strs = ["cooldown1", "cooldown2", "cooldown3"]
    keys = [boa.eval(f'keccak256("{k}")') for k in key_strs]
    durations = [3600, 7200, 10800]

    for key, duration in zip(keys, durations):
        cooldown_test_contract.test_add(key, duration)

    expected_timestamp = boa.env.timestamp
    for key_str, expected_duration in zip(key_strs, durations):
        start, stored_duration = get_cooldown(cooldown_test_contract, key_str)
        assert start == expected_timestamp
        assert stored_duration == expected_duration


@given(
    duration=st.integers(min_value=1, max_value=2**128 - 1),
    key=st.binary(min_size=32, max_size=32),
)
def test_add_fuzz_valid_inputs(cooldown_test_contract, duration, key):
    cooldown_test_contract.test_add(key, duration)

    start, stored_duration = cooldown_test_contract.get_cooldown_raw(key)
    assert start == boa.env.timestamp
    assert stored_duration == duration


@given(
    duration=st.integers(min_value=2**128, max_value=2**256 - 1),
    key=st.binary(min_size=32, max_size=32),
)
def test_add_fuzz_large_duration(cooldown_test_contract, duration, key):
    with boa.reverts("duration too large"):
        cooldown_test_contract.test_add(key, duration)


def test_add_timestamp_accuracy(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')
    duration = 3600

    timestamp_before = boa.env.timestamp
    cooldown_test_contract.test_add(key, duration)
    timestamp_after = boa.env.timestamp

    start, _ = cooldown_test_contract.get_cooldown_raw(key)
    assert timestamp_before <= start <= timestamp_after


def test_add_edge_case_max_duration(cooldown_test_contract):
    key = boa.eval('keccak256("test_cooldown")')
    max_duration = 2**128 - 1

    cooldown_test_contract.test_add(key, max_duration)

    start, stored_duration = cooldown_test_contract.get_cooldown_raw(key)
    assert start == boa.env.timestamp
    assert stored_duration == max_duration


def test_add_empty_key(cooldown_test_contract):
    key = b"\0" * 32
    duration = 3600

    cooldown_test_contract.test_add(key, duration)

    start, stored_duration = cooldown_test_contract.get_cooldown_raw(key)
    assert start == boa.env.timestamp
    assert stored_duration == duration
