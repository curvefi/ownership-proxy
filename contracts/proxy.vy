# pragma version 0.4.3

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

# TODO make module friendly
from contracts.interfaces import IProxy

implements: IProxy

from curve_std import error as e

ZeroAddress: constant(Bytes[4]) = method_id("ZeroAddress()")
InvalidDelegationDuration: constant(Bytes[4]) = method_id("InvalidDelegationDuration()")
InvalidChecker: constant(Bytes[4]) = method_id("InvalidChecker()")

DAO_ROLE: public(constant(bytes32)) = keccak256("DAO_ROLE")
EMERGENCY_ADMIN_ROLE: public(constant(bytes32)) = keccak256("EMERGENCY_ADMIN_ROLE")


# TODO figure our right size 
MAX_OUTSIZE: constant(uint256) = 32 * 10000
MAX_CALLDATA_SIZE: constant(uint256) = 1234

delegations: public(HashMap[address, IProxy.DelegationMetadata])
target: public(address)

@deploy
def __init__(target: address, dao: address):
    e.require(target != empty(address), ZeroAddress)
    e.require(dao != empty(address), ZeroAddress)

    access_control.__init__()
    access_control._revoke_role(access_control.DEFAULT_ADMIN_ROLE, msg.sender)
    access_control._grant_role(access_control.DEFAULT_ADMIN_ROLE, dao)
    access_control._grant_role(DAO_ROLE, dao)
    self.target = target


@external
@payable
@raw_return
def __default__() -> Bytes[MAX_OUTSIZE]:
    metadata: IProxy.DelegationMetadata = self.delegations[msg.sender]

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
    _delegate: address,
    _metadata: IProxy.DelegationMetadata,
    ):
    access_control._check_role(DAO_ROLE, msg.sender)

    e.require(_delegate != empty(address), ZeroAddress)
    e.require(_metadata.checker != empty(address), ZeroAddress)
    e.require(_metadata.end_ts > block.timestamp, InvalidDelegationDuration)
    e.require(_metadata.checker.codehash != empty(bytes32), InvalidChecker)

    self.delegations[_delegate] = _metadata

    log IProxy.DelegationSet(
        delegate=_delegate,
        end_ts=_metadata.end_ts,
        checker=_metadata.checker
    )

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
    self.delegations[delegate] = empty(IProxy.DelegationMetadata)

    log IProxy.DelegationKilled(delegate=delegate)
