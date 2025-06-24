import boa
from tests.utils.constants import ZERO_ADDRESS


def test_check_owner(proxy):
    alice = boa.env.generate_address()

    with boa.reverts("access_control: account is missing role"):
        proxy.set_delegation(boa.env.eoa, boa.env.timestamp + 1, b'0000', ZERO_ADDRESS, sender=alice)


def test_delegate_non_zero(proxy):
    with boa.reverts("delegate==0x0"):
        proxy.set_delegation(boa.eval("empty(address)"), boa.env.timestamp + 1, b'0000', ZERO_ADDRESS)


def test_delegation_expired(proxy):
    with boa.reverts("end_ts<=block.timestamp"):
        proxy.set_delegation(boa.env.eoa, boa.env.timestamp, b'0000', ZERO_ADDRESS)


def test_default_behavior(proxy):
    FUNC_SIG = b'1234'
    END_TS = boa.env.timestamp + 1
    proxy.set_delegation(boa.env.eoa, END_TS, FUNC_SIG, ZERO_ADDRESS)
    assert proxy.delegations(FUNC_SIG, boa.env.eoa) == (END_TS, ZERO_ADDRESS)


    