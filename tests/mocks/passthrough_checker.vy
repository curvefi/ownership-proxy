# pragma version 0.4.3
from contracts import proxy

CALLDATA_SLICE: constant(uint256) = 2 * 256

calldata: DynArray[Bytes[CALLDATA_SLICE], 5000]


@external
@payable
def __default__():
    # Accept all calls, just record them
    self.calldata.append(slice(msg.data, 0, CALLDATA_SLICE))


@external
@view
def call_count() -> uint256:
    return len(self.calldata)
