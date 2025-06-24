# pragma version 0.4.3

from contracts.permissions import cooldown
from contracts.permissions import interval
from contracts.permissions import whitelist

initializes: cooldown
initializes: interval
initializes: whitelist


FOO_INTERVAL: constant(bytes32) = keccak256("FOO_INTERVAL")
FOO_COOLDOWN: constant(bytes32) = keccak256("FOO_COOLDOWN")
FOO_WHITELIST: constant(bytes32) = keccak256("FOO_WHITELIST")

@deploy
def __init__():
    cooldown.add_from_days(FOO_COOLDOWN, 2)
    interval.add(FOO_INTERVAL, 100, 200)
    whitelist.add_multiple(FOO_WHITELIST, [
        0x1234567890123456789012345678901234567890,
        0x0987654321098765432109876543210987654321
    ])

def foo(addy: address, amount: uint256):
    cooldown.check_and_reset(FOO_COOLDOWN)
    interval.check(FOO_INTERVAL, amount)
    whitelist.check(FOO_WHITELIST, addy)
