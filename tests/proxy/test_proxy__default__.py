import boa
from tests.utils.constants import ZERO_ADDRESS


def test_no_delegation_requires_dao_role(proxy, dummy):
    """Test that calls without delegation require DAO_ROLE"""
    # Try to call without any delegation or role
    unauthorized_user = boa.env.generate_address()
    
    with boa.env.prank(unauthorized_user):
        with boa.reverts("access_control: account is missing role"): 
            dummy.at(proxy.address).some_func()


def test_with_dao_role_no_delegation(proxy, dummy, dao):
    """Test that DAO_ROLE can call without delegation"""
    result = dummy.at(proxy.address).some_func(sender=dao)
    assert result == 42


def test_delegation_with_deny_all_checker(proxy, dummy, dao, deny_all_checker):
    """Test that delegation with deny_all_checker blocks the call"""
    delegated_user = boa.env.generate_address()
    
    # Set delegation with deny_all_checker
    proxy.set_delegation(
        delegated_user,
        boa.env.timestamp + 1000,
        deny_all_checker,
        sender=dao
    )
    
    # Call should fail because checker denies all calls
    with boa.env.prank(delegated_user):
        with boa.reverts("Checker denied"):
            dummy.at(proxy.address).some_func()



def test_delegation_with_accept_all_checker(proxy, dummy, dao, accept_all_checker):
    """Test that delegation with accept_all_checker allows the call"""
    delegated_user = boa.env.generate_address()
    
    # Set delegation with accept_all_checker
    proxy.set_delegation(
        delegated_user,
        boa.env.timestamp + 1000,
        accept_all_checker,
        sender=dao
    )
    
    # Call should succeed because checker accepts all calls
    with boa.env.prank(delegated_user):
        result = dummy.at(proxy.address).some_func()
        assert result == 42


def test_delegation_with_empty_checker(proxy, dummy, dao):
    """Test that delegation with empty checker (no __default__) denies the call"""
    delegated_user = boa.env.generate_address()
    
    # Deploy an empty checker contract (no __default__ function)
    empty_checker_source = """# pragma version 0.4.3

# Empty contract - no __default__ function
"""
    empty_checker = boa.loads(empty_checker_source)
    
    # Set delegation with empty checker
    proxy.set_delegation(
        delegated_user,
        boa.env.timestamp + 1000,
        empty_checker,
        sender=dao
    )
    
    # Call should fail because checker has no __default__ to handle the call
    with boa.env.prank(delegated_user):
        with boa.reverts():  # Empty checker will cause a revert
            dummy.at(proxy.address).some_func()


def test_default_payable_forwarding(proxy, dummy, dao, accept_all_checker):
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
    payable_proxy = boa.load("contracts/proxy.vy", payable_target.address, dao)
    
    # Grant DAO_ROLE to the default EOA for testing
    DAO_ROLE = payable_proxy.DAO_ROLE()
    payable_proxy.grantRole(DAO_ROLE, boa.env.eoa, sender=dao)
    
    # Set up delegation
    payable_proxy.set_delegation(
        boa.env.eoa,
        boa.env.timestamp + 1000,
        accept_all_checker,
        sender=dao
    )
    
    # Send ETH through proxy
    eth_amount = 10**18  # 1 ETH
    boa.env.set_balance(boa.env.eoa, eth_amount * 2)
    
    result = payable_target.at(payable_proxy.address).receive_eth(value=eth_amount)
    assert result == eth_amount
    assert payable_target.balance_received() == eth_amount
    assert boa.env.get_balance(payable_target.address) == eth_amount


def test_default_with_large_return_data(proxy, dao, accept_all_checker):
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
    large_proxy = boa.load("contracts/proxy.vy", large_return_contract.address, dao)
    
    # Grant DAO_ROLE to the default EOA for testing
    DAO_ROLE = large_proxy.DAO_ROLE()
    large_proxy.grantRole(DAO_ROLE, boa.env.eoa, sender=dao)
    
    # Set up delegation
    large_proxy.set_delegation(
        boa.env.eoa,
        boa.env.timestamp + 1000,
        accept_all_checker,
        sender=dao
    )
    
    # Call and verify large return data
    result = large_return_contract.at(large_proxy.address).get_large_array()
    assert len(result) == 5000
    assert result[0] == 0
    assert result[4999] == 4999


def test_default_delegation_boundary_timestamp(proxy, dummy, dao, accept_all_checker):
    """Test delegation at exact timestamp boundary"""
    current_time = boa.env.timestamp
    
    # Create a new account without DAO role
    delegate = boa.env.generate_address()
    
    # Set delegation to expire at specific timestamp
    expiry_time = current_time + 1000
    proxy.set_delegation(
        delegate,
        expiry_time,
        accept_all_checker,
        sender=dao
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