
import itertools
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, \
    Sequence, Tuple, Union, cast

# mypy bytePipe.py

# {{{ types

BpAddr = int
BpValue = int
BpAddrs = Sequence[BpAddr]
BpValues = Sequence[BpValue]
BpAddrValue = Tuple[BpAddr, BpValue]
BpAddrValues = Sequence[BpAddrValue]

# Specific type for the values of the whole addressable range (128B).
BpMem = \
    Tuple[BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue,
          BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue, BpValue]

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

def bpReset(device) -> None: # {{{
    '''Reset BytePipe FSM to a known/idle state.

    Most extreme case where a write burst has been initiated and expecting
    to receive 256 bytes.
    These 256 bytes may be write burst data (to an unknown address), or
    commands to read address 0 when there is no write burst outstanding.
    To prevent buffer levels causing too much backpressure, must intersperse
    writes with reads which are allowed to timeout.
    '''

    deviceTimeout = device.timeout
    device.timeout = 0.01

    for i in range(256):
        try:
            _ = bpReadSequential(device, [0])
        except:
            pass

    device.timeout = deviceTimeout

    return
# }}} def bpReset

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

def bpReadPoll(device, addrs:BpAddrs) -> Iterator[BpAddrValue]: # {{{

    cyclicAddrs = itertools.cycle(addrs)
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
            ret:BpAddrValue = (addrs[i-1], value)
            yield ret

# }}} def bpReadPoll

def bpReadAddr(device, addr:int, nBytes:int) -> BpValues: # {{{
    '''Perform a stream of burst reads from the same location.

    It is intended that some locations are backed by a FIFO, so this allows the
    bandwidth of the underlying channel (USB, RS232, I2C, SPI, etc) to be used
    efficiently.
    The underlying channel is assumed to produce data in quantites of whole
    bytes.
    '''
    assert isinstance(addr, int), (type(addr), addr)
    assert 1 <= addr < 128, addr

    assert isinstance(nBytes, int), (type(nBytes), nBytes)
    assert 0 <= nBytes, nBytes

    maxBurstRd = 255

    nMaxBursts, lastLength = divmod(nBytes, maxBurstRd)
    assert lastLength < 255

    ret_ = []
    for _ in range(nMaxBursts):

        # Initialize burst downcounter.
        addrValue0:BpAddrValue = bpWriteSequential(device, [(0, maxBurstRd)])[0]
        value0:BpValue = addrValue0[1]

        # Send read command.
        assert 1 == device.write(bytes([addr]))

        # Retreive bytes.
        bs = device.read(maxBurstRd+1)
        assert (maxBurstRd+1) == len(bs), (maxBurstRd+1, len(bs), bs)
        assert value0 == int(bs[0])

        # Drop the first byte which is the config/status value at address 0.
        r = [int(b) for b in bs][1:]
        assert maxBurstRd == len(r), (maxBurstRd, len(r), r)

        ret_ += r

    # Burst overhead is nBytes+5.
    # Single overhead is nBytes*2, (+1 if address is not setup).
    minEfficentBurst = 5

    if 0 == lastLength:
        pass

    elif lastLength >= minEfficentBurst:
        # Another burst

        # Initialize burst downcounter.
        addrValue0:BpAddrValue = bpWriteSequential(device, [(0, lastLength)])[0]
        value0:BpValue = addrValue0[1]

        # Send read command.
        assert 1 == device.write(bytes([addr]))

        # Retreive bytes.
        bs = device.read(lastLength+1)
        assert (lastLength+1) == len(bs), (lastLength+1, len(bs), bs)
        assert value0 == int(bs[0])

        # Drop the first byte which is the config/status value at address 0.
        r = [int(b) for b in bs][1:]
        assert lastLength == len(r), (lastLength, len(r), r)

        ret_ += r

    elif nMaxBursts != 0:
        # Sequential, where address has already been setup.
        for _ in range(lastLength):
            # Send read command
            assert 1 == device.write(bytes([addr]))

            # Retreive single byte.
            ret_ += [int(b) for b in device.read(1)]

    else:
        addrValues = bpReadSequential(device, [addr]*lastLength)
        ret_ += [v for a,v in addrValues]

    assert nBytes == len(ret_), (nBytes, len(ret_), ret_)
    return ret_
# }}} def bpReadAddr

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
