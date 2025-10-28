import pytest
import boa


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
def deny_all_checker():
    """A checker contract that denies all calls with a specific reason"""
    source = """# pragma version 0.4.3

@external
@payable
def __default__():
    raise "Checker denied"
"""
    return boa.loads(source)


@pytest.fixture
def accept_all_checker():
    """A checker contract that accepts all calls"""
    source = """# pragma version 0.4.3

@external
@payable
def __default__():
    # Accept all calls - do nothing
    pass
"""
    return boa.loads(source)
