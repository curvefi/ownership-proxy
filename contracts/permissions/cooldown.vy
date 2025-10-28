# pragma version 0.4.3


event CooldownSet:
    key: indexed(bytes32)
    start: uint256
    duration: uint256


event CooldownReset:
    key: indexed(bytes32)
    new_start: uint256


struct Cooldown:
    # vyper does not yet have packing, just being forward looking here
    start: uint128
    duration: uint128


cooldowns: public(HashMap[bytes32, Cooldown])


@internal
def add(key: bytes32, duration: uint256, override: bool = False):
    assert duration > 0, "duration must be positive"
    assert duration < 2**128, "duration too large"

    cd: Cooldown = self.cooldowns[key]
    if cd.start + cd.duration != 0:
        assert override, "cooldown already exists"


    # Add the new cooldown
    self.cooldowns[key] = Cooldown(
        start=convert(block.timestamp, uint128), duration=convert(duration, uint128)
    )

    log CooldownSet(key=key, start=block.timestamp, duration=duration)


@internal
def add_from_hours(key: bytes32, duration_hours: uint256, override: bool = False):
    self.add(key, duration_hours * 3600, override)


@internal
def add_from_days(key: bytes32, duration_days: uint256, override: bool = False):
    self.add(key, duration_days * 86400, override)


@internal
def check_and_reset(key: bytes32, suppress_log: bool = False):
    cd: Cooldown = self.cooldowns[key]
    cd_end: uint256 = convert(cd.start + cd.duration, uint256)
    assert block.timestamp >= cd_end, "cooldown not expired"

    # Reset the cooldown
    self.cooldowns[key].start = convert(block.timestamp, uint128)

    if not suppress_log:
        log CooldownReset(key=key, new_start=block.timestamp)
