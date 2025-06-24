import pytest
import boa
from tests.utils.constants import ZERO_ADDRESS


def test_default_no_delegation_requires_dao_role(proxy, dummy):
    """Test that calls without delegation require DAO_ROLE"""
    # Try to call without any delegation or role
    unauthorized_user = boa.env.generate_address()
    
    with boa.env.prank(unauthorized_user):
        with boa.reverts():  # Should revert due to lack of DAO_ROLE
            dummy.at(proxy.address).some_func()


def test_default_with_dao_role_no_delegation(proxy, dummy):
    """Test that DAO_ROLE can call without delegation"""
    dao_user = boa.env.generate_address()
    
    # Grant DAO_ROLE
    DAO_ROLE = proxy.DAO_ROLE()
    proxy.grantRole(DAO_ROLE, dao_user)
    
    # Should succeed with DAO_ROLE even without delegation
    with boa.env.prank(dao_user):
        result = dummy.at(proxy.address).some_func()
        assert result == 42


def test_default_expired_delegation_requires_dao_role(proxy, dummy):
    """Test that expired delegation falls back to DAO_ROLE check"""
    delegated_user = boa.env.generate_address()
    func_data = dummy.some_func.prepare_calldata()
    
    # Set delegation that expires immediately
    proxy.set_delegation(
        delegated_user,
        boa.env.timestamp + 1,  # Expires in 1 second
        func_data[:4],
        ZERO_ADDRESS
    )
    
    # Time travel past expiration
    boa.env.time_travel(seconds=2)
    
    # Should fail without DAO_ROLE
    with boa.env.prank(delegated_user):
        with boa.reverts():
            dummy.at(proxy.address).some_func()
    
    # Grant DAO_ROLE and retry
    DAO_ROLE = proxy.DAO_ROLE()
    proxy.grantRole(DAO_ROLE, delegated_user)
    
    with boa.env.prank(delegated_user):
        result = dummy.at(proxy.address).some_func()
        assert result == 42


def test_default_payable_forwarding(proxy, dummy):
    """Test that __default__ correctly forwards ETH value"""
    # Deploy a contract that receives ETH
    payable_target_source = """# pragma version 0.4.3

balance_received: public(uint256)

@external
@payable
def receive_eth() -> uint256:
    self.balance_received = msg.value
    return msg.value
"""
    payable_target = boa.loads(payable_target_source)
    
    # Deploy proxy pointing to payable target
    payable_proxy = boa.load("contracts/proxy.vy", payable_target.address)
    
    # Grant DAO_ROLE to the default EOA for testing
    DAO_ROLE = payable_proxy.DAO_ROLE()
    payable_proxy.grantRole(DAO_ROLE, boa.env.eoa)
    
    # Set up delegation
    func_data = payable_target.receive_eth.prepare_calldata()
    payable_proxy.set_delegation(
        boa.env.eoa,
        boa.env.timestamp + 1000,
        func_data[:4],
        ZERO_ADDRESS
    )
    
    # Send ETH through proxy
    eth_amount = 10**18  # 1 ETH
    boa.env.set_balance(boa.env.eoa, eth_amount * 2)
    
    result = payable_target.at(payable_proxy.address).receive_eth(value=eth_amount)
    assert result == eth_amount
    assert payable_target.balance_received() == eth_amount
    assert boa.env.get_balance(payable_target.address) == eth_amount


def test_default_with_large_return_data(proxy):
    """Test __default__ with return data approaching MAX_OUTSIZE"""
    # Deploy contract that returns large data
    large_return_source = """# pragma version 0.4.3

@external
@view
def get_large_array() -> DynArray[uint256, 5000]:
    result: DynArray[uint256, 5000] = []
    for i: uint256 in range(5000):
        result.append(i)
    return result
"""
    large_return_contract = boa.loads(large_return_source)
    
    # Deploy proxy for this contract
    large_proxy = boa.load("contracts/proxy.vy", large_return_contract.address)
    
    # Grant DAO_ROLE to the default EOA for testing
    DAO_ROLE = large_proxy.DAO_ROLE()
    large_proxy.grantRole(DAO_ROLE, boa.env.eoa)
    
    # Set up delegation
    func_data = large_return_contract.get_large_array.prepare_calldata()
    large_proxy.set_delegation(
        boa.env.eoa,
        boa.env.timestamp + 1000,
        func_data[:4],
        ZERO_ADDRESS
    )
    
    # Call and verify large return data
    result = large_return_contract.at(large_proxy.address).get_large_array()
    assert len(result) == 5000
    assert result[0] == 0
    assert result[4999] == 4999


def test_default_delegation_boundary_timestamp(proxy, dummy):
    """Test delegation at exact timestamp boundary"""
    func_data = dummy.some_func.prepare_calldata()
    current_time = boa.env.timestamp
    
    # Create a new account without DAO role
    delegate = boa.env.generate_address()
    
    # Set delegation to expire at specific timestamp
    expiry_time = current_time + 1000
    proxy.set_delegation(
        delegate,
        expiry_time,
        func_data[:4],
        ZERO_ADDRESS
    )
    
    # Time travel to one second before expiry - should work
    boa.env.time_travel(seconds=999)
    with boa.env.prank(delegate):
        result = dummy.at(proxy.address).some_func()
        assert result == 42
    
    # Time travel to exact expiry time - should NOT work (expires at timestamp, not after)
    boa.env.time_travel(seconds=1)
    
    with boa.env.prank(delegate):
        with boa.reverts("access_control: account is missing role"):  # No DAO role, delegation expired
            dummy.at(proxy.address).some_func()


def test_default_with_malicious_checker(proxy, dummy):
    """Test proxy behavior with various malicious checker behaviors"""
    # Checker that tries to modify state
    state_modifying_checker = boa.loads("""
# pragma version 0.4.3

counter: public(uint256)

@external
def __default__():
    self.counter += 1
    # Try to call back to proxy (reentrancy attempt)
    raw_call(msg.sender, msg.data)
""")
    
    func_data = dummy.some_func.prepare_calldata()
    proxy.set_delegation(
        boa.env.eoa,
        boa.env.timestamp + 1000,
        func_data[:4],
        state_modifying_checker.address
    )
    
    # This should revert due to reentrancy in checker
    with boa.reverts():
        dummy.at(proxy.address).some_func()