import boa
from tests.utils.constants import ZERO_ADDRESS


def test_call_forwarding(proxy, dummy, caller):
    data = dummy.some_func.prepare_calldata()

    proxy.set_delegation(caller.address, boa.env.timestamp + 1000, data[:4], ZERO_ADDRESS)

    assert caller.call_simple(proxy.address) == 42


def test_casting_interface(proxy, proxy_as_dummy):
    data = proxy_as_dummy.some_func.prepare_calldata()

    proxy.set_delegation(boa.env.eoa, boa.env.timestamp + 1000, data[:4], ZERO_ADDRESS)

    assert proxy_as_dummy.some_func() == 42


def test_address_bitmask(proxy, proxy_as_dummy):
    addy = "0xC907ba505C2E1cbc4658c395d4a2c7E6d2c32656"
    data = proxy_as_dummy.something_fancier.prepare_calldata(addy)

    proxy.set_delegation(boa.env.eoa, boa.env.timestamp + 1000, data[:4], ZERO_ADDRESS)
    assert proxy_as_dummy.something_fancier(addy) == addy


def test_return_tuple(proxy, proxy_as_dummy):
    data = proxy_as_dummy.tuples.prepare_calldata()
    proxy.set_delegation(boa.env.eoa, boa.env.timestamp + 1000, data[:4], ZERO_ADDRESS)
    assert proxy_as_dummy.tuples() == (69, proxy.address)
