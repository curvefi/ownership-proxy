import pytest
import boa


@pytest.fixture(scope="module")
def whitelist_test_contract():
    source = """
# pragma version 0.4.3

from contracts.permissions import whitelist

initializes: whitelist

@external
def test_add(key: bytes32, addr: address):
    whitelist.add(key, addr)

@external
def test_check(key: bytes32, addr: address):
    whitelist.check(key, addr)
"""
    return boa.loads(source)


def test_check_whitelisted_address_passes(whitelist_test_contract):
    key = boa.eval('keccak256("test_check")')
    addr = boa.env.generate_address()

    # Add address to whitelist
    whitelist_test_contract.test_add(key, addr)

    # Check should pass without reverting
    whitelist_test_contract.test_check(key, addr)


def test_check_non_whitelisted_address_reverts(whitelist_test_contract):
    key = boa.eval('keccak256("test_not_whitelisted")')
    addr = boa.env.generate_address()

    with boa.reverts("address not whitelisted"):
        whitelist_test_contract.test_check(key, addr)


def test_check_different_key_reverts(whitelist_test_contract):
    key1 = boa.eval('keccak256("test_key1")')
    key2 = boa.eval('keccak256("test_key2")')
    addr = boa.env.generate_address()

    # Add to key1
    whitelist_test_contract.test_add(key1, addr)

    # Check with key2 should revert
    with boa.reverts("address not whitelisted"):
        whitelist_test_contract.test_check(key2, addr)


def test_check_zero_address(whitelist_test_contract):
    key = boa.eval('keccak256("test_zero")')
    zero_addr = "0x0000000000000000000000000000000000000000"

    # Should revert for non-whitelisted zero address
    with boa.reverts("address not whitelisted"):
        whitelist_test_contract.test_check(key, zero_addr)

    # Add zero address
    whitelist_test_contract.test_add(key, zero_addr)

    # Now check should pass
    whitelist_test_contract.test_check(key, zero_addr)
