# pragma version 0.4.1
from snekmate.auth import ownable

# TODO figure out the amount
MAX_RESTRICTION_MASK: constant(uint256) = 100

struct RestrictionMask:
    offset: uint256
    mask: bytes32

struct DelegationInfo:
    delegate: address
    end_ts: uint256
    restrictions: DynArray[RestrictionMask, MAX_RESTRICTION_MASK]

restrictions: public(HashMap[bytes4, HashMap[address, DelegationInfo]])

MAX_OUTSIZE: constant(uint256) = 32

initializes: ownable
implements: ownable.__interface__
exports: (
    ownable.owner,
    ownable.renounce_ownership,
    ownable.transfer_ownership,
)

target: address

@deploy
def __init__(target: address):
    self.target = target
    ownable.__init__()


@internal
def _is_delegate(info: DelegationInfo) -> bool:
    assert info.delegate != empty(address), "delegate not set"
    assert info.end_ts > block.timestamp, "delegation expired"
    for r: RestrictionMask in info.restrictions:
        offset: uint256 = r.offset
        mask: uint256 = convert(r.mask, uint256)
        offset_start: uint256 = 4 + offset * 32

        data_to_check: uint256 = convert(slice(msg.data, offset_start, 32), uint256)
        assert (
            data_to_check & mask == mask
        ), "restrictions not met"
    return True


@internal
def _is_owner() -> bool:
    return msg.sender == ownable.owner
    

@external
def __default__() -> Bytes[MAX_OUTSIZE]:
    func_sig: bytes4 = convert(slice(msg.data, 0, 4), bytes4)
    info: DelegationInfo = self.restrictions[func_sig][msg.sender]

    assert self._is_delegate(info) or self._is_owner(), "unauthorized"

    result: Bytes[MAX_OUTSIZE] = b""
    result = raw_call(self.target, msg.data, max_outsize=MAX_OUTSIZE)
    return result


@external
def set_delegation(
    delegate: address,
    end_ts: uint256,
    func_sig: bytes4,
    restrictions: DynArray[RestrictionMask, MAX_RESTRICTION_MASK]
    ):

    ownable._check_owner()

    assert delegate != empty(address), "delegate cannot be empty"
    assert end_ts > block.timestamp, "end timestamp must be in the future"

    prev_offset: uint256 = 0
    for r: RestrictionMask in restrictions:
        prev_offset = r.offset

    self.restrictions[func_sig][msg.sender] = DelegationInfo(
        delegate=delegate,
        end_ts=end_ts,
        restrictions=restrictions
    )
    

