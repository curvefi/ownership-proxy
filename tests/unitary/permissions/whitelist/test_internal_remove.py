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
def test_remove(key: bytes32, addr: address):
    whitelist.remove(key, addr)

@external
@view
def is_whitelisted(key: bytes32, addr: address) -> bool:
    return whitelist.whitelist[key][addr]
"""
    return boa.loads(source)


def test_remove_basic(whitelist_test_contract):
    key = boa.eval('keccak256("test_remove")')
    addr = boa.env.generate_address()

    # First add the address
    whitelist_test_contract.test_add(key, addr)
    assert whitelist_test_contract.is_whitelisted(key, addr) == True

    # Then remove it
    whitelist_test_contract.test_remove(key, addr)
    assert whitelist_test_contract.is_whitelisted(key, addr) == False


def test_remove_non_whitelisted_reverts(whitelist_test_contract):
    key = boa.eval('keccak256("test_not_whitelisted")')
    addr = boa.env.generate_address()

    with boa.reverts("address not whitelisted"):
        whitelist_test_contract.test_remove(key, addr)


def test_remove_already_removed_reverts(whitelist_test_contract):
    key = boa.eval('keccak256("test_already_removed")')
    addr = boa.env.generate_address()

    # Add and remove the address
    whitelist_test_contract.test_add(key, addr)
    whitelist_test_contract.test_remove(key, addr)

    # Try to remove again
    with boa.reverts("address not whitelisted"):
        whitelist_test_contract.test_remove(key, addr)


def test_remove_different_keys_isolated(whitelist_test_contract):
    key1 = boa.eval('keccak256("test_key1")')
    key2 = boa.eval('keccak256("test_key2")')
    addr = boa.env.generate_address()

    # Add to both keys
    whitelist_test_contract.test_add(key1, addr)
    whitelist_test_contract.test_add(key2, addr)

    # Remove from key1
    whitelist_test_contract.test_remove(key1, addr)

    # Check that key1 is removed but key2 is still whitelisted
    assert whitelist_test_contract.is_whitelisted(key1, addr) == False
    assert whitelist_test_contract.is_whitelisted(key2, addr) == True
