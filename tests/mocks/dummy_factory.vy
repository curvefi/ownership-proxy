# pragma version 0.4.3

addy: public(address)


@external
def some_func() -> uint256:
    return 42


@external
def something_fancier(target: address) -> address:
    return target


@external
def tuples() -> (uint256, address):
    return 69, msg.sender
