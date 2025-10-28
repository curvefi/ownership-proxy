import boa
from tests.utils.constants import ZERO_ADDRESS


def test_kill_delegation_basic(proxy, dao, deny_all_checker):
    func_sig = b"test"
    delegate = boa.env.generate_address()

    # First set a delegation
    proxy.set_delegation(
        delegate, boa.env.timestamp + 1000, deny_all_checker, sender=dao
    )

    # Verify delegation exists
    end_ts, stored_checker = proxy.delegations(delegate)
    assert end_ts > boa.env.timestamp
    assert stored_checker == deny_all_checker.address

    # Kill the delegation
    proxy.kill_delegation(func_sig, delegate, sender=dao)

    # Verify delegation is killed
    end_ts, stored_checker = proxy.delegations(delegate)
    assert end_ts == 0
    assert stored_checker == ZERO_ADDRESS


def test_kill_delegation_requires_dao_role(proxy, dao, deny_all_checker):
    func_sig = b"test"
    delegate = boa.env.generate_address()
    alice = boa.env.generate_address()

    # Set a delegation
    proxy.set_delegation(
        delegate, boa.env.timestamp + 1000, deny_all_checker, sender=dao
    )

    # Try to kill without DAO_ROLE
    with boa.reverts("access_control: account is missing role"):
        proxy.kill_delegation(func_sig, delegate, sender=alice)


def test_kill_nonexistent_delegation(proxy, dao):
    func_sig = b"test"
    delegate = boa.env.generate_address()

    # Kill non-existent delegation (should not revert)
    proxy.kill_delegation(func_sig, delegate, sender=dao)

    # Verify it's still empty
    end_ts, stored_checker = proxy.delegations(delegate)
    assert end_ts == 0
    assert stored_checker == ZERO_ADDRESS


def test_emergency_kill_delegation_basic(proxy, dao, deny_all_checker):
    func_sig = b"test"
    delegate = boa.env.generate_address()
    emergency_admin = boa.env.generate_address()

    # Grant EMERGENCY_ADMIN_ROLE
    EMERGENCY_ADMIN_ROLE = proxy.EMERGENCY_ADMIN_ROLE()
    proxy.grantRole(EMERGENCY_ADMIN_ROLE, emergency_admin, sender=dao)

    # Set a delegation
    proxy.set_delegation(
        delegate, boa.env.timestamp + 1000, deny_all_checker, sender=dao
    )

    # Emergency kill the delegation
    proxy.emergency_kill_delegation(func_sig, delegate, sender=emergency_admin)

    # Verify delegation is killed
    end_ts, stored_checker = proxy.delegations(delegate)
    assert end_ts == 0
    assert stored_checker == ZERO_ADDRESS


def test_emergency_kill_requires_emergency_admin_role(proxy, dao, deny_all_checker):
    func_sig = b"test"
    delegate = boa.env.generate_address()
    alice = boa.env.generate_address()

    # Set a delegation
    proxy.set_delegation(
        delegate, boa.env.timestamp + 1000, deny_all_checker, sender=dao
    )

    # Try to emergency kill without EMERGENCY_ADMIN_ROLE
    with boa.reverts("access_control: account is missing role"):
        proxy.emergency_kill_delegation(func_sig, delegate, sender=alice)


def test_kill_delegation_with_checker(proxy, dao, deny_all_checker):
    func_sig = b"test"
    delegate = boa.env.generate_address()

    # Set a delegation with a checker
    proxy.set_delegation(
        delegate, boa.env.timestamp + 1000, deny_all_checker, sender=dao
    )

    # Verify delegation exists with checker
    end_ts, stored_checker = proxy.delegations(delegate)
    assert end_ts > boa.env.timestamp
    assert stored_checker == deny_all_checker.address

    # Kill the delegation
    proxy.kill_delegation(func_sig, delegate, sender=dao)

    # Verify both end_ts and checker are reset
    end_ts, stored_checker = proxy.delegations(delegate)
    assert end_ts == 0
    assert stored_checker == ZERO_ADDRESS


def test_multiple_delegations_isolated(proxy, dao, deny_all_checker):
    func_sig1 = b"test"
    func_sig2 = b"data"
    delegate1 = boa.env.generate_address()
    delegate2 = boa.env.generate_address()

    # Set multiple delegations
    proxy.set_delegation(
        delegate1, boa.env.timestamp + 1000, deny_all_checker, sender=dao
    )
    proxy.set_delegation(
        delegate2, boa.env.timestamp + 1000, deny_all_checker, sender=dao
    )
    proxy.set_delegation(
        delegate1, boa.env.timestamp + 1000, deny_all_checker, sender=dao
    )

    # Kill one specific delegation
    proxy.kill_delegation(func_sig1, delegate1, sender=dao)

    # Verify only the specific delegation is killed
    end_ts1, _ = proxy.delegations(delegate1)
    assert end_ts1 == 0

    # Others should still exist
    end_ts2, _ = proxy.delegations(delegate2)
    assert end_ts2 > boa.env.timestamp

    # Note: Since delegations are per-delegate (not per func_sig),
    # killing delegate1 kills it for all function signatures
    # The third delegation was overwritten when we set delegate1 again
