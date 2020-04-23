
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, \
    Tuple, Union, cast

# {{{ types

BpAddrs = Sequence[int]
BpAddrValues = Sequence[Tuple[int, int]]

# Specific type for the values of the whole addressable range (128B).
BpMem = Tuple[int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int,
              int, int, int, int, int, int, int, int]

# }}} types

def bpAddrValuesToMem(addrValues:BpAddrValues) -> BpMem: # {{{

    ret_:List[int] = [-1]*128
    for addr,value in addrValues:
        assert isinstance(addr, int), (type(addr), addr)
        assert 0 <= addr < 128, addr
        assert isinstance(value, int), (type(value), value)
        assert 0 <= value < 256, value
        ret_[addr] = value

    assert isinstance(ret_, list), (type(ret_), ret_)
    assert 128 == len(ret_), (len(ret_), ret_)
    ret:BpMem = cast(BpMem, tuple(ret_))

    assert isinstance(ret, tuple), (type(ret), ret)
    assert 128 == len(ret), (len(ret), ret)

    return ret
# }}} def bpAddrValuesToMem

def bpReadSequential(device, addrs:BpAddrs) -> BpAddrValues: # {{{

    ret_ = []
    for i,addr in enumerate(addrs):

        # Send read command
        assert isinstance(addr, int), (type(addr), addr)
        assert 0 <= addr < 128, (i, addr)
        assert 1 == device.write(bytes([addr]))

        value:int = ord(device.read(1))

        # First return value is discarded.
        if 0 == i:
            continue
        else:
            ret_.append((addrs[i-1], value))

    # Last address/value.
    assert 1 == device.write(bytes([addrs[-1]]))
    ret_.append((addrs[-1], ord(device.read(1))))

    # Finalize return value.
    ret = tuple(ret_)

    assert len(ret) == len(addrs), (ret, addrs)
    assert all((a == ra) for a,(ra,rv) in zip(addrs, ret))
    assert all((rv < 256) for ra,rv in ret)

    return ret
# }}} def bpReadSequential

def bpWriteSequential(device, addrValues:BpAddrValues) -> BpAddrValues: # {{{

    ret_ = []
    for i,(addr,value) in enumerate(addrValues):

        # Send write command
        assert isinstance(addr, int), (type(addr), addr)
        assert 0 <= addr < 128, (i, addr)
        assert 2 == device.write(bytes([addr + 128, value]))

        ret_.append((addr, ord(device.read(1))))

    # Finalize return value.
    ret:BpAddrValues = tuple(ret_)

    assert len(ret) == len(addrValues), (ret, addrValues)
    assert all((a == ra) for (a,v),(ra,rv) in zip(addrValues, ret))
    assert all((rv < 256) for ra,rv in ret)

    return ret
# }}} def bpWriteSequential

def bpPrintMem(title:str, mem:BpMem) -> None: # {{{

    print(title.strip() + ':')

    # Increasing left-to-right and top-to-bottom.
    # Text of 16 lines of 8 bytes.
    for i in range(16):
        base = i*8
        values = [mem[base + offset] for offset in range(8)]

        line = ' '.join("--" if v < 0 else ("%02x" % v) \
                        for v in values)

        print("  %3d .. %3d: %s" % (base, base+7, line))

    return
# }}} def bpPrintMem
