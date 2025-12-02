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

from ownership_proxy.interfaces import IProxy

implements: IProxy

DAO_ROLE: constant(bytes32) = keccak256("DAO_ROLE")
EMERGENCY_ADMIN_ROLE: constant(bytes32) = keccak256("EMERGENCY_ADMIN_ROLE")

# TODO figure our right size 
MAX_OUTSIZE: constant(uint256) = 32 * 10000
MAX_CALLDATA_SIZE: constant(uint256) = 1234

delegations: HashMap[address, IProxy.DelegationMetadata]
TARGET: immutable(address)


@deploy
def __init__(_target: address, _dao: address):
    assert _target != empty(address), "empty target"
    assert _dao != empty(address), "empty dao"

    access_control.__init__()
    access_control._revoke_role(access_control.DEFAULT_ADMIN_ROLE, msg.sender)
    access_control._grant_role(access_control.DEFAULT_ADMIN_ROLE, _dao)
    access_control._grant_role(DAO_ROLE, _dao)
    TARGET = _target


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
    result = raw_call(TARGET, msg.data, value=msg.value, max_outsize=MAX_OUTSIZE)
    return result


@external
def proxy__set_delegation(
    _delegate: address,
    _metadata: IProxy.DelegationMetadata,
    ):
    access_control._check_role(DAO_ROLE, msg.sender)

    assert _delegate != empty(address), "empty delegate"
    assert _metadata.checker != empty(address), "empty checker"
    assert _metadata.end_ts > block.timestamp, "invalid delegation duration"
    assert _metadata.checker.codehash != empty(bytes32), "invalid checker"

    self.delegations[_delegate] = _metadata

    log IProxy.DelegationSet(
        delegate=_delegate,
        end_ts=_metadata.end_ts,
        checker=_metadata.checker
    )


@internal
def _kill_delegation(_func_sig: bytes4, _delegate: address):
    self.delegations[_delegate] = empty(IProxy.DelegationMetadata)

    log IProxy.DelegationKilled(delegate=_delegate)


@external
def proxy__kill_delegation(_func_sig: bytes4, _delegate: address):
    access_control._check_role(DAO_ROLE, msg.sender)
    self._kill_delegation(_func_sig, _delegate)


# TODO underscore args
@external
def proxy__emergency_kill_delegation(_func_sig: bytes4, _delegate: address):
    access_control._check_role(EMERGENCY_ADMIN_ROLE, msg.sender)
    self._kill_delegation(_func_sig, _delegate)


@external
@view
def proxy__delegations(_delegate: address) -> IProxy.DelegationMetadata:
    return self.delegations[_delegate]


@external
@view
def proxy__target() -> address:
    return TARGET


@external
@pure
def proxy__DAO_ROLE() -> bytes32:
    return DAO_ROLE


@external
@pure
def proxy__EMERGENCY_ADMIN_ROLE() -> bytes32:
    return EMERGENCY_ADMIN_ROLE