import pytest
import boa

from tests.utils.deployers import PASSTHROUGH_CHECKER_DEPLOYER


@pytest.fixture
def dummy():
    return boa.load("tests/mocks/dummy_factory.vy")


@pytest.fixture
def dao():
    return boa.env.generate_address("dao")


@pytest.fixture
def proxy(dummy, dao):
    return boa.load("contracts/proxy.vy", dummy.address, dao)


@pytest.fixture
def proxy_as_dummy(proxy, dummy):
    # TODO make a helper to generate this by ABI fusion (so it doesn't trigger a warning)
    return dummy.at(proxy.address)


@pytest.fixture
def caller():
    return boa.load("tests/mocks/caller.vy")



@pytest.fixture
def passthrough_checker():
    return PASSTHROUGH_CHECKER_DEPLOYER.deploy()

