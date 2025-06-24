interface Factory:
    def some_func() -> uint256: nonpayable


@external
def call_simple(factory: Factory) -> uint256:
    return extcall factory.some_func()
