import pytest
import boa
from tests.utils.constants import ZERO_ADDRESS


@pytest.fixture
def mock_checker():
    """Deploy a mock checker contract that validates calls"""
    source = """# pragma version 0.4.3

call_count: public(uint256)

@external
@payable
def __default__():
    # Simple checker that just counts calls
    self.call_count += 1
"""
    return boa.loads(source)


def test_default_with_checker_validation(proxy, dummy, mock_checker):
    """Test that __default__ calls the checker when delegation is active"""
    # Set up delegation with a checker
    func_data = dummy.some_func.prepare_calldata()
    func_sig = func_data[:4]
    
    proxy.set_delegation(
        boa.env.eoa, 
        boa.env.timestamp + 1000, 
        func_sig, 
        mock_checker.address
    )
    
    # Call through proxy
    result = dummy.at(proxy.address).some_func()
    assert result == 42
    
    # Verify checker was called
    assert mock_checker.call_count() == 1


def test_default_with_checker_revert(proxy, dummy):
    """Test that __default__ reverts if checker reverts"""
    # Deploy a checker that always reverts
    reverting_checker_source = """# pragma version 0.4.3

@external
def __default__():
    raise "Checker validation failed"
"""
    reverting_checker = boa.loads(reverting_checker_source)
    
    # Set up delegation with reverting checker
    func_data = dummy.some_func.prepare_calldata()
    func_sig = func_data[:4]
    
    proxy.set_delegation(
        boa.env.eoa, 
        boa.env.timestamp + 1000, 
        func_sig, 
        reverting_checker.address
    )
    
    # Call should revert due to checker
    with boa.reverts("Checker validation failed"):
        dummy.at(proxy.address).some_func()


def test_default_with_conditional_checker(proxy, dummy):
    """Test checker that validates based on call parameters"""
    # Deploy a checker that validates specific conditions
    conditional_checker_source = """# pragma version 0.4.3

@external
def __default__():
    # For testing something_fancier function which takes an address
    if len(msg.data) >= 36:  # 4 bytes sig + 32 bytes address
        # Extract the address parameter (bytes 4-36)
        param_bytes: bytes32 = convert(slice(msg.data, 4, 32), bytes32)
        param_addr: address = convert(param_bytes, address)
        
        # Only allow specific addresses
        assert param_addr != 0x0000000000000000000000000000000000000000, "Zero address not allowed"
"""
    conditional_checker = boa.loads(conditional_checker_source)
    
    # Set up delegation for something_fancier function
    test_addr = "0xC907ba505C2E1cbc4658c395d4a2c7E6d2c32656"
    func_data = dummy.something_fancier.prepare_calldata(test_addr)
    func_sig = func_data[:4]
    
    proxy.set_delegation(
        boa.env.eoa,
        boa.env.timestamp + 1000,
        func_sig,
        conditional_checker.address
    )
    
    # Valid call should succeed
    result = dummy.at(proxy.address).something_fancier(test_addr)
    assert result == test_addr
    
    # Call with zero address should fail
    with boa.reverts("Zero address not allowed"):
        dummy.at(proxy.address).something_fancier(ZERO_ADDRESS)


def test_default_multiple_delegations_different_checkers(proxy, dummy):
    """Test multiple delegations with different checkers"""
    # Deploy two different checkers
    checker1_source = """# pragma version 0.4.3

call_count: public(uint256)

@external
def __default__():
    self.call_count += 1
"""
    
    checker2_source = """# pragma version 0.4.3

call_count: public(uint256)

@external 
def __default__():
    self.call_count += 2  # Different increment to distinguish
"""
    
    checker1 = boa.loads(checker1_source)
    checker2 = boa.loads(checker2_source)
    
    # Set up different delegations with different checkers
    func1_data = dummy.some_func.prepare_calldata()
    func2_data = dummy.tuples.prepare_calldata()
    
    # Different users with different checkers
    user1 = boa.env.generate_address()
    user2 = boa.env.generate_address()
    
    proxy.set_delegation(user1, boa.env.timestamp + 1000, func1_data[:4], checker1.address)
    proxy.set_delegation(user2, boa.env.timestamp + 1000, func2_data[:4], checker2.address)
    
    # Call as user1
    with boa.env.prank(user1):
        dummy.at(proxy.address).some_func()
    assert checker1.call_count() == 1
    assert checker2.call_count() == 0
    
    # Call as user2
    with boa.env.prank(user2):
        dummy.at(proxy.address).tuples()
    assert checker1.call_count() == 1
    assert checker2.call_count() == 2


