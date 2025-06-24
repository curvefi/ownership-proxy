import pytest
import boa


@pytest.fixture
def dummy():
    return boa.load("tests/mocks/dummy_factory.vy")


@pytest.fixture
def proxy(dummy):
    proxy = boa.load("contracts/proxy.vy", dummy.address)
    # Grant DAO_ROLE to the default EOA for testing
    DAO_ROLE = proxy.DAO_ROLE()
    proxy.grantRole(DAO_ROLE, boa.env.eoa)
    return proxy

@pytest.fixture
def proxy_as_dummy(proxy, dummy):
    # TODO make a helper to generate this by ABI fusion (so it doesn't trigger a warning)
    return dummy.at(proxy.address)


@pytest.fixture
def caller():
    return boa.load("tests/mocks/caller.vy")