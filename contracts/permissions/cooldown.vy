# pragma version 0.4.3

# TODO make module friendly
from contracts.interfaces import ICooldown

cooldowns: public(HashMap[bytes32, ICooldown.Cooldown])


@internal
def add(key: bytes32, duration: uint256, override: bool = False):
    assert duration > 0, "duration must be positive"
    assert duration < 2**128, "duration too large"

    cd: ICooldown.Cooldown = self.cooldowns[key]
    if cd.start + cd.duration != 0:
        assert override, "cooldown already exists"


    # Add the new cooldown
    self.cooldowns[key] = ICooldown.Cooldown(
        start=convert(block.timestamp, uint128), duration=convert(duration, uint128)
    )

    log ICooldown.CooldownSet(key=key, start=block.timestamp, duration=duration)


@internal
def add_from_hours(key: bytes32, duration_hours: uint256, override: bool = False):
    self.add(key, duration_hours * 3600, override)


@internal
def add_from_days(key: bytes32, duration_days: uint256, override: bool = False):
    self.add(key, duration_days * 86400, override)


@internal
def check_and_reset(key: bytes32, log_reset: bool = False):
    cd: ICooldown.Cooldown = self.cooldowns[key]
    cd_end: uint256 = convert(cd.start + cd.duration, uint256)
    assert block.timestamp >= cd_end, "cooldown not expired"

    # Reset the cooldown
    self.cooldowns[key].start = convert(block.timestamp, uint128)

    # Might be useful in some cases
    if log_reset:
        log ICooldown.CooldownReset(key=key, new_start=block.timestamp)
