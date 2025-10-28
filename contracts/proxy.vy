# pragma version 0.4.3

from ethereum.ercs import IERC165

from snekmate.auth import access_control
initializes: access_control
implements: access_control.__interface__
exports: (
    access_control.DEFAULT_ADMIN_ROLE,
    access_control.getRoleAdmin,
    access_control.grantRole,
    access_control.hasRole,
    access_control.renounceRole,
    access_control.revokeRole,
    access_control.set_role_admin,
    access_control.supportsInterface
)

event DelegationSet:
    delegate: indexed(address)
    end_ts: uint256
    checker: indexed(address)

event DelegationKilled:
    delegate: indexed(address)

struct DelegationMetadata:
    # TODO pack
    end_ts: uint256
    checker: address

DAO_ROLE: public(constant(bytes32)) = keccak256("DAO_ROLE")
EMERGENCY_ADMIN_ROLE: public(constant(bytes32)) = keccak256("EMEREGENCY_ADMIN_ROLE")


MAX_OUTSIZE: constant(uint256) = 32 * 10000
MAX_CALLDATA_SIZE: constant(uint256) = 1234

delegations: public(HashMap[address, DelegationMetadata])
target: public(address)

@deploy
def __init__(target: address, dao: address):
    assert target != empty(address), "target==0x0"

    access_control.__init__()
    access_control._revoke_role(access_control.DEFAULT_ADMIN_ROLE, msg.sender)
    access_control._grant_role(access_control.DEFAULT_ADMIN_ROLE, dao)
    access_control._grant_role(DAO_ROLE, dao)
    self.target = target


@external
@payable
@raw_return
def __default__() -> Bytes[MAX_OUTSIZE]:
    func_sig: bytes4 = convert(slice(msg.data, 0, 4), bytes4)
    metadata: DelegationMetadata = self.delegations[msg.sender]

    is_delegate: bool = metadata.end_ts > block.timestamp
    if is_delegate:
        raw_call(metadata.checker, msg.data)
    else:
        access_control._check_role(DAO_ROLE, msg.sender)

    result: Bytes[MAX_OUTSIZE] = b""
    result = raw_call(self.target, msg.data, value=msg.value, max_outsize=MAX_OUTSIZE)
    return result


@external
def set_delegation(
    delegate: address,
    end_ts: uint256,
    checker: address
    ):

    access_control._check_role(DAO_ROLE, msg.sender)

    assert delegate != empty(address), "delegate==0x0"
    assert end_ts > block.timestamp, "end_ts<=block.timestamp"
    assert checker != empty(address), "checker==0x0"
    assert checker.codehash != empty(bytes32), "checker has no code"

    self.delegations[delegate] = DelegationMetadata(
        end_ts=end_ts,
        checker=checker
    )

    log DelegationSet(delegate=delegate, end_ts=end_ts, checker=checker)

@external
def kill_delegation(func_sig: bytes4, delegate: address):
    access_control._check_role(DAO_ROLE, msg.sender)
    self._kill_delegation(func_sig, delegate)


@external
def emergency_kill_delegation(func_sig: bytes4, delegate: address):
    access_control._check_role(EMERGENCY_ADMIN_ROLE, msg.sender)
    self._kill_delegation(func_sig, delegate)


@internal
def _kill_delegation(func_sig: bytes4, delegate: address):
    self.delegations[delegate] = DelegationMetadata(
        end_ts=0,
        checker=empty(address)
    )

    log DelegationKilled(delegate=delegate)
