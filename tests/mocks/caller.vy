interface Factory:
    def some_func() -> uint256: nonpayable

@external
def call_simple(factory: Factory): 
    print(extcall factory.some_func())

