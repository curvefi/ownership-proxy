# pragma version 0.4.3

event AddressWhitelisted:
    key: indexed(bytes32)
    addr: indexed(address)

event AddressRemovedFromWhitelist:
    key: indexed(bytes32)
    addr: indexed(address)

whitelist: HashMap[bytes32, HashMap[address, bool]]
whitelist_array: HashMap[bytes32, DynArray[address, MAX_WHITELIST_SIZE]]

MAX_WHITELIST_SIZE: constant(uint256) = 1000


@internal
def add(key: bytes32, addr: address, override: bool = False):
    
    if self.whitelist[key][addr]:
        assert override, "address already whitelisted"
    
    # Add the address to the whitelist
    self.whitelist[key][addr] = True
    
    log AddressWhitelisted(key=key, addr=addr)


@internal
def add_multiple(key: bytes32, addrs: DynArray[address, MAX_WHITELIST_SIZE], override: bool = False):
    assert len(addrs) > 0, "no addresses provided"

    for addr: address in addrs:
        self.add(key, addr, override)

    


@internal
def remove(key: bytes32, addr: address):
    assert self.whitelist[key][addr], "address not whitelisted"
    
    # Remove the address from the whitelist
    self.whitelist[key][addr] = False
    
    log AddressRemovedFromWhitelist(key=key, addr=addr)


@internal
def check(key: bytes32, addr: address):
    # Check if the address is whitelisted for the given key
    assert self.whitelist[key][addr], "address not whitelisted"
