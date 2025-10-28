import boa


def test_call_forwarding(proxy, dummy, caller, dao, accept_all_checker):
    proxy.set_delegation(
        caller.address, boa.env.timestamp + 1000, accept_all_checker, sender=dao
    )

    assert caller.call_simple(proxy.address) == 42


def test_casting_interface(proxy, proxy_as_dummy, dao, accept_all_checker):
    proxy.set_delegation(
        boa.env.eoa, boa.env.timestamp + 1000, accept_all_checker, sender=dao
    )

    assert proxy_as_dummy.some_func() == 42


def test_address_bitmask(proxy, proxy_as_dummy, dao, accept_all_checker):
    addy = "0xC907ba505C2E1cbc4658c395d4a2c7E6d2c32656"

    proxy.set_delegation(
        boa.env.eoa, boa.env.timestamp + 1000, accept_all_checker, sender=dao
    )
    assert proxy_as_dummy.something_fancier(addy) == addy


def test_return_tuple(proxy, proxy_as_dummy, dao, accept_all_checker):
    proxy.set_delegation(
        boa.env.eoa, boa.env.timestamp + 1000, accept_all_checker, sender=dao
    )
    assert proxy_as_dummy.tuples() == (69, proxy.address)
