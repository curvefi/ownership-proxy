# pragma version 0.4.3

# TODO make module friendly
from contracts.interfaces import IInterval

implements: IInterval


intervals: public(HashMap[bytes32, IInterval.Interval])
# min = 0 and max = 0 can be a valid interval, so we need to track if an interval exists
interval_exists: HashMap[bytes32, bool]


@internal
def add(key: bytes32, lb: uint256, ub: uint256, override: bool = False):
    r: IInterval.Interval = self.intervals[key]

    if self.interval_exists[key]:
        assert override, "interval already exists"


    # Validate that lower bound is not greater than upper bound
    assert lb <= ub, "inverted range: lb > ub"

    # Add the new interval
    self.intervals[key] = IInterval.Interval(lb=lb, ub=ub)
    self.interval_exists[key] = True

    log IInterval.IntervalSet(key=key, lb=lb, ub=ub)


@internal
def add_singleton(key: bytes32, _value: uint256, override: bool = False):
    self.add(key, _value, _value, override)


@internal
@view
def check(key: bytes32, _value: uint256):
    r: IInterval.Interval = self.intervals[key]
    assert self.interval_exists[key], "interval does not exist"

    # Check if the value is within the interval
    assert r.lb <= _value and _value <= r.ub, "value out of interval"
