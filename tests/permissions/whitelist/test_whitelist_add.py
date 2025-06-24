import pytest
import boa
from hypothesis import given, strategies as st


@pytest.fixture(scope="module")
def whitelist_test_contract():
    source = """
# pragma version 0.4.3

from contracts.permissions import whitelist

initializes: whitelist

@external
def test_add(key: bytes32, addr: address, override: bool = False):
    whitelist.add(key, addr, override)

@external
def test_add_multiple(key: bytes32, addrs: DynArray[address, 1000], override: bool = False):
    whitelist.add_multiple(key, addrs, override)

@external
@view
def is_whitelisted(key: bytes32, addr: address) -> bool:
    return whitelist.whitelist[key][addr]
"""
    return boa.loads(source)


def test_add_basic(whitelist_test_contract):
    key = boa.eval('keccak256("test_whitelist")')
    addr = boa.env.generate_address()
    
    whitelist_test_contract.test_add(key, addr)
    
    assert whitelist_test_contract.is_whitelisted(key, addr) == True


def test_add_multiple_addresses(whitelist_test_contract):
    key = boa.eval('keccak256("test_multiple")')
    addrs = [boa.env.generate_address() for _ in range(5)]
    
    whitelist_test_contract.test_add_multiple(key, addrs)
    
    for addr in addrs:
        assert whitelist_test_contract.is_whitelisted(key, addr) == True


def test_add_existing_without_override_reverts(whitelist_test_contract):
    key = boa.eval('keccak256("test_existing")')
    addr = boa.env.generate_address()
    
    whitelist_test_contract.test_add(key, addr)
    
    with boa.reverts("address already whitelisted"):
        whitelist_test_contract.test_add(key, addr, False)


def test_add_existing_with_override_succeeds(whitelist_test_contract):
    key = boa.eval('keccak256("test_override")')
    addr = boa.env.generate_address()
    
    whitelist_test_contract.test_add(key, addr)
    whitelist_test_contract.test_add(key, addr, True)
    
    assert whitelist_test_contract.is_whitelisted(key, addr) == True


def test_add_multiple_empty_list_reverts(whitelist_test_contract):
    key = boa.eval('keccak256("test_empty")')
    
    with boa.reverts("no addresses provided"):
        whitelist_test_contract.test_add_multiple(key, [])


def test_add_multiple_with_duplicates_and_override(whitelist_test_contract):
    key = boa.eval('keccak256("test_duplicates")')
    addr = boa.env.generate_address()
    addrs = [addr, addr]  # Duplicate addresses
    
    whitelist_test_contract.test_add_multiple(key, addrs, True)
    
    assert whitelist_test_contract.is_whitelisted(key, addr) == True


def test_add_zero_address(whitelist_test_contract):
    key = boa.eval('keccak256("test_zero")')
    zero_addr = "0x0000000000000000000000000000000000000000"
    
    whitelist_test_contract.test_add(key, zero_addr)
    
    assert whitelist_test_contract.is_whitelisted(key, zero_addr) == True


@given(
    key=st.binary(min_size=32, max_size=32),
    num_addrs=st.integers(min_value=1, max_value=10)
)
def test_add_multiple_fuzz(whitelist_test_contract, key, num_addrs):
    addrs = [boa.env.generate_address() for _ in range(num_addrs)]
    
    whitelist_test_contract.test_add_multiple(key, addrs)
    
    for addr in addrs:
        assert whitelist_test_contract.is_whitelisted(key, addr) == True