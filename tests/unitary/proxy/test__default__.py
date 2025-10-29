import boa

def test_default_behavior_owner(proxy_as_dummy, dao):
    """Dao is the sender"""
    result = proxy_as_dummy.some_func(sender=dao)
    assert result == 42

def test_default_behavior_delegate(proxy, proxy_as_dummy, passthrough_checker, dao):
    """Authorized delegate is the sender, checker is mocked and accepts any msg.data"""
    delegated_user = boa.env.generate_address("delegate")
    
    # Set delegation with accept_all_checker
    proxy.set_delegation(
        delegated_user,
        (boa.env.timestamp + 1,
        passthrough_checker),
        sender=dao
    )
    
    # Call should succeed because checker accepts all calls
    result = proxy_as_dummy.some_func(sender=delegated_user)
    assert result == 42
    # TODO check calldata
    assert passthrough_checker.call_count() == 1 


def test_unauthorized(proxy_as_dummy):
    """No DAO role, no delegation"""
    with boa.reverts("access_control: account is missing role"): 
        proxy_as_dummy.some_func()


def test_default_payable_forwarding():
    """Test that __default__ correctly forwards ETH value"""
    # TODO
    pass


def test_default_with_large_return_data():
    """Test __default__ with return data greater than MAX_OUTSIZE"""
    # TODO
    pass
    