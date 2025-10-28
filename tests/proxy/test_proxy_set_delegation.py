import boa
from tests.utils.constants import ZERO_ADDRESS


def test_check_owner(proxy, dao, deny_all_checker):
    alice = boa.env.generate_address()

    with boa.reverts("access_control: account is missing role"):
        proxy.set_delegation(
            boa.env.eoa, boa.env.timestamp + 1, deny_all_checker, sender=alice
        )


def test_delegate_non_zero(proxy, dao, deny_all_checker):
    with boa.reverts("delegate==0x0"):
        proxy.set_delegation(
            boa.eval("empty(address)"),
            boa.env.timestamp + 1,
            deny_all_checker,
            sender=dao,
        )


def test_delegation_expired(proxy, dao, deny_all_checker):
    with boa.reverts("end_ts<=block.timestamp"):
        proxy.set_delegation(
            boa.env.eoa, boa.env.timestamp, deny_all_checker, sender=dao
        )


def test_checker_non_zero(proxy, dao):
    with boa.reverts("checker==0x0"):
        proxy.set_delegation(
            boa.env.eoa, boa.env.timestamp + 1, ZERO_ADDRESS, sender=dao
        )


def test_default_behavior(proxy, dao, deny_all_checker):
    END_TS = boa.env.timestamp + 1

    proxy.set_delegation(boa.env.eoa, END_TS, deny_all_checker, sender=dao)
    stored_end_ts, stored_checker = proxy.delegations(boa.env.eoa)
    assert stored_end_ts == END_TS
    assert stored_checker == deny_all_checker.address
