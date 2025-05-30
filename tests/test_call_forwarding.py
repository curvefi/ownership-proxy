import boa
import pytest


@pytest.fixture
def dummy():
    return boa.load("tests/mocks/dummy_factory.vy")

@pytest.fixture
def proxy(dummy):
    return boa.load("contracts/ownership_proxy.vy", dummy)

@pytest.fixture
def caller():
    return boa.load("tests/mocks/caller.vy")

def test_call_forwarding(proxy, dummy, caller):
    data = dummy.some_func.prepare_calldata()

    print(data)

    proxy.set_delegation(boa.env.eoa, boa.env.timestamp + 1000, data[:4], ([], []))
    proxy.env.raw_call(proxy.address, data=data)

    caller.call_simple(proxy)

def test_address_bitmask(proxy, dummy):
    addy = "0xC907ba505C2E1cbc4658c395d4a2c7E6d2c32656"
    data = dummy.something_fancier.prepare_calldata(addy)

    address_bytes = bytes.fromhex(addy[2:])
    restrictions = ([0], [address_bytes])

    proxy.set_delegation(boa.env.eoa, boa.env.timestamp + 1000, data[:4], restrictions)
    proxy.env.raw_call(proxy.address, data=data)





