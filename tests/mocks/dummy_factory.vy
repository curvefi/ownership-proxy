# pragma version 0.4.1

addy: public(address)

@external
def some_func() -> uint256:
    return 42

@external
def something_fancier(target: address):
    self.addy = target
    
