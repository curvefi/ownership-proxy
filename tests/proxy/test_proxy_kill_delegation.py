import pytest
import boa
from tests.utils.constants import ZERO_ADDRESS


def test_kill_delegation_basic(proxy):
    func_sig = b'test'
    delegate = boa.env.generate_address()
    
    # First set a delegation
    proxy.set_delegation(delegate, boa.env.timestamp + 1000, func_sig, ZERO_ADDRESS)
    
    # Verify delegation exists
    end_ts, checker = proxy.delegations(func_sig, delegate)
    assert end_ts > boa.env.timestamp
    assert checker == ZERO_ADDRESS
    
    # Kill the delegation
    proxy.kill_delegation(func_sig, delegate)
    
    # Verify delegation is killed
    end_ts, checker = proxy.delegations(func_sig, delegate)
    assert end_ts == 0
    assert checker == ZERO_ADDRESS
    

def test_kill_delegation_requires_dao_role(proxy):
    func_sig = b'test'
    delegate = boa.env.generate_address()
    alice = boa.env.generate_address()
    
    # Set a delegation
    proxy.set_delegation(delegate, boa.env.timestamp + 1000, func_sig, ZERO_ADDRESS)
    
    # Try to kill without DAO_ROLE
    with boa.reverts("access_control: account is missing role"):
        proxy.kill_delegation(func_sig, delegate, sender=alice)


def test_kill_nonexistent_delegation(proxy):
    func_sig = b'test'
    delegate = boa.env.generate_address()
    
    # Kill non-existent delegation (should not revert)
    proxy.kill_delegation(func_sig, delegate)
    
    # Verify it's still empty
    end_ts, checker = proxy.delegations(func_sig, delegate)
    assert end_ts == 0
    assert checker == ZERO_ADDRESS


def test_emergency_kill_delegation_basic(proxy):
    func_sig = b'test'
    delegate = boa.env.generate_address()
    emergency_admin = boa.env.generate_address()
    
    # Grant EMERGENCY_ADMIN_ROLE
    EMERGENCY_ADMIN_ROLE = proxy.EMERGENCY_ADMIN_ROLE()
    proxy.grantRole(EMERGENCY_ADMIN_ROLE, emergency_admin)
    
    # Set a delegation
    proxy.set_delegation(delegate, boa.env.timestamp + 1000, func_sig, ZERO_ADDRESS)
    
    # Emergency kill the delegation
    proxy.emergency_kill_delegation(func_sig, delegate, sender=emergency_admin)
    
    # Verify delegation is killed
    end_ts, checker = proxy.delegations(func_sig, delegate)
    assert end_ts == 0
    assert checker == ZERO_ADDRESS



def test_emergency_kill_requires_emergency_admin_role(proxy):
    func_sig = b'test'
    delegate = boa.env.generate_address()
    alice = boa.env.generate_address()
    
    # Set a delegation
    proxy.set_delegation(delegate, boa.env.timestamp + 1000, func_sig, ZERO_ADDRESS)
    
    # Try to emergency kill without EMERGENCY_ADMIN_ROLE
    with boa.reverts("access_control: account is missing role"):
        proxy.emergency_kill_delegation(func_sig, delegate, sender=alice)


def test_kill_delegation_with_checker(proxy):
    func_sig = b'test'
    delegate = boa.env.generate_address()
    checker_address = boa.env.generate_address()
    
    # Set a delegation with a checker
    proxy.set_delegation(delegate, boa.env.timestamp + 1000, func_sig, checker_address)
    
    # Verify delegation exists with checker
    end_ts, checker = proxy.delegations(func_sig, delegate)
    assert end_ts > boa.env.timestamp
    assert checker == checker_address
    
    # Kill the delegation
    proxy.kill_delegation(func_sig, delegate)
    
    # Verify both end_ts and checker are reset
    end_ts, checker = proxy.delegations(func_sig, delegate)
    assert end_ts == 0
    assert checker == ZERO_ADDRESS


def test_multiple_delegations_isolated(proxy):
    func_sig1 = b'test'
    func_sig2 = b'data'
    delegate1 = boa.env.generate_address()
    delegate2 = boa.env.generate_address()
    
    # Set multiple delegations
    proxy.set_delegation(delegate1, boa.env.timestamp + 1000, func_sig1, ZERO_ADDRESS)
    proxy.set_delegation(delegate2, boa.env.timestamp + 1000, func_sig1, ZERO_ADDRESS)
    proxy.set_delegation(delegate1, boa.env.timestamp + 1000, func_sig2, ZERO_ADDRESS)
    
    # Kill one specific delegation
    proxy.kill_delegation(func_sig1, delegate1)
    
    # Verify only the specific delegation is killed
    end_ts1, _ = proxy.delegations(func_sig1, delegate1)
    assert end_ts1 == 0
    
    # Others should still exist
    end_ts2, _ = proxy.delegations(func_sig1, delegate2)
    assert end_ts2 > boa.env.timestamp
    
    end_ts3, _ = proxy.delegations(func_sig2, delegate1)
    assert end_ts3 > boa.env.timestamp