#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import sys, os, time
import argparse
try: import queue
except ImportError: import Queue as queue

curdir = os.path.dirname(os.path.abspath(sys.argv[0]))
try:
  import ust_misc as um
except ImportError:
  libdirs = [d for d in (os.path.join(curdir, '..', 'lib'), \
                         os.path.join(curdir, 'python', 'lib')) \
             if os.path.isdir(d)]
  if libdirs: sys.path.append(libdirs[0])

import ust_misc as um
import ust_target as ut

def create_session(usb_clk_ghz = 1.0 / 26): # {{{
  um.cl_args = sys.argv[1:]
  um.check_udagent_env(curdir)

  session = ut.UstSession()
  session.start()
  session.set_udb_clk_freq(usb_clk_ghz)
  session.apply_initial_configuration()

  return session
# }}} def create_session

s = None#create_session()

class tinn(): # {{{
    '''Magic constants and addresses copied from tinn.h
    '''

    PATH_ACPU_ELF = "riscv/temp/tinn.acpu.x"
    PATH_SCPU_ELF = "riscv/temp/tinn.scpu.x"
    PATH_ACPU_BIN = "riscv/bin/tinn.acpu.bin"
    PATH_SCPU_BIN = "riscv/bin/tinn.scpu.bin"
    PATH_ASCIIDATASET = "resources/apps/tinn/semeion.data"

    PATH_SI_LOG = "log.si.txt"
    PATH_SI_VCD = "tinn1.vcd"

    # Initial values for PC set by session.get_jpam(initialise=True) using
    # values from session._cpu_start_addr()
    _START_ACPU             = 0x60000000
    _START_SCPU             = 0x70000000

    # Magic location for each core to signal the host via load/stores.
    HOSTFLAG_ACPU           = 0x50000000
    HOSTFLAG_SCPU           = 0x50000008

    # Address of Inter-Core Communication flags controlling run state.
    TOSLV_CMD               = 0x50001000
    TOMST_REQ               = 0x50001008

    # Address of pointers to message Inter-Core Communication buffers.
    TOSLV_BUFFADDR          = 0x50001010
    TOMST_BUFFADDR          = 0x50001018
    TOMST_BINBUFFADDR       = 0x50001020

    # ASCII data loaded into memory separately at known address.
    ASCIIDATASET_ADDR       = 0x51000000

    TAYGETE_AXI_COMMUNICATOR= 0xC0000000
    TAYGETE_STATIC_INSTR    = 0xC0010000
    TAYGETE_VIRTUAL_CONSOLE = 0xC0020000
# }}} class tinn

def toline_sinst_data(msg, axi_id_w=7, human=True): # {{{
    '''Return string for a single STIN message.
    '''
    # Time reported as a hex string.
    msgtime = int(msg.meta["time"], 16)
    if human:
        metastr = "%s@%d:" % (msg.module, msgtime)
    else:
        metastr = "%d" % msgtime

    fields = {str(k):v.value for (k,v) in msg.fields.items()}

    size = fields["size"] + 1
    channel = fields["channel"]
    event = fields["event"]
    flag = fields["flag"]

    chstr = (" ch%d" % channel) if human else (" %d" % channel)
    flagstr = " FLAG" if flag else ""

    if fields["id_present"]:
        infrastructure_id = int(fields["data"] & (2**axi_id_w-1))
        data = fields["data"] >> axi_id_w
        mststr = " mst=%d" % infrastructure_id
    else:
        data = fields["data"]
        mststr = ""

    if event or flag:
        datastr = ""
    else:
        data = data & (2**(size*8)-1)
        datastr = (" data=0x%x" % data) if human else (" 0x%x" % data)

    return "".join([metastr, chstr, flagstr, datastr, mststr])
# }}} def toline_sinst_data

def proc_sinst(fd=sys.stdout, maxnum=10000, keepother=True, session=s): # {{{
    '''Print and discard SI data messages like si_readlines, and classify any
       other type of message.
    '''
    seen_msgs = 0
    while seen_msgs < maxnum:
        try:
            (meta, msg) = session.mstream.msgs.get(False)
            msg.meta = meta
            seen_msgs += 1
        except queue.Empty:
            break

        if session._check_msg_type(msg, "sinst_data"):
            print(toline_sinst_data(msg, human=False), file=fd)
        elif keepother:
            session._classify_msg(msg)

    return seen_msgs
# }}} def proc_sinst

def si_readlines(fd=sys.stdout, session=s, axi_id_w=7): # {{{
    '''Print lines from all SI (Static Instrumentation) modules to an open file,
    default append to STDOUT.
    Returns a dict keyed by SI modules, each with a list of lines.

    Line format is "<SI module>: <data line>".

    E.g. To extract all lines from si1 the client should read all of the SI
    lines with something like:
        log = open("log.si.txt", 'w')
        si_readlines(log, session)
        ... maybe more calls to si_readlines ...
        log.close()
    And the host may do something like this:
        grep 'si1: ' log.si.txt
    '''
    cs = session.MSG_CLASS_SI_DATA
    cmsgs = session.cmsgs

    si_modules = [md for md in sorted(cmsgs.keys()) if cs in cmsgs[md]]

    ret = {}
    for md in si_modules:
        #ret[md] = cmsgs[md][cs]
        ret[md] = cmsgs[md].pop(cs)

    if fd is not None:
        for md,msgs in ret.items():
            for msg in msgs:

                print(toline_sinst_data(msg, axi_id_w=axi_id_w), file=fd)

        fd.flush()
        os.fsync(fd)

    return ret
# }}} def si_readlines

def vc_readlines(fd=sys.stdout, session=s): # {{{
    '''Print lines from all VC (Virtual Console) modules to an open file,
    default append to STDOUT.
    Returns a dict keyed by VC channels, each with a list of lines.

    Line format is "<VC module>.<channel number>: <printf'ed line>".
    This is similar to ust_target.py:UstSession.handle_vc() except the output
    can be split by grepping on the first chararcters.

    E.g. To extract all lines from vc1 channel 0 (ACPU on Taygete) the client
    should read all of the VC lines with something like:
        log = open("log.vc.txt", 'w')
        _ = vc_readlines(log, session)
        ... maybe more calls to vc_readlines ...
        log.close()
    And the host may do something like this:
        grep 'vc1.0: ' log.vc.txt
    '''
    ret = {}

    for (m, ch) in sorted(session.vci.keys()):
        vci = session.vci[(m, ch)]
        s = (vci.vc_string + session.vcread(m, ch)).replace("\r", "")
        lines = s.split("\n")
        vci.vc_string = lines.pop()

        chnm = "{}.{}".format(m, ch)
        ret[chnm] = lines

    if fd is not None:
        for chnm,lines in ret.items():
            for line in lines:
                print(chnm + ": " + line, file=fd)

        fd.flush()
        os.fsync(fd)

    return ret
# }}} def vc_readlines

def pprint_rsp(rsp): # {{{

    if type(rsp) is list:
        msgs = rsp
    elif type(rsp) is ut.msg_codec.MsgObj:
        msgs = [rsp]
    else:
        assert False, rsp

    import pprint
    for m in msgs:
        assert type(m) is ut.msg_codec.MsgObj
        pprint.pprint(m.fields.items())
# }}} def pprint_rsp

def get_msg(md="foo", msg="get_bar", fields={}, session=s): # {{{
    rsp = session.send_get_msg_with_response(md,
        session.blank_us_ctrl_fields(md, msg))
    return rsp
# }}} def get_msg

def write_si_mailbox(session=s, # {{{
    md="si1",
    channel=0,
    mailbox=0,
    wrdata=0xDEADBEEF,
    module_addr=tinn.TAYGETE_STATIC_INSTR,
    verbose=True):

    rsp_discovery = session.send_get_msg_with_response(md,
        session.blank_us_ctrl_fields(md, "discovery_request"))[0].fields.items()
    base_addr = [d.value for s,d in rsp_discovery if s == "base_addr"][0]

    # UL-001174-TR-3B-Static Instrumentation User Guide.pdf
    channel_address = base_addr + (0x200 * channel)
    addrN = channel_address + (0x10 * mailbox)
    final_addr = module_addr + addrN

    is_timestamp    = (mailbox & (1 << 0)) != 0
    is_flag         = (mailbox & (1 << 1)) != 0
    is_marked       = (mailbox & (1 << 2)) != 0
    is_blocking     = (mailbox & (1 << 3)) != 0
    is_event        = (mailbox & (1 << 4)) != 0

    if verbose:

        print("write_si_mailbox() WRITE")
        print("    md=%s" % md)
        print("    channel=%d" % channel)
        print("    mailbox=%d" % mailbox)
        print("    wrdata=%s -> final_addr=%s" % (hex(wrdata), hex(final_addr)))
        print("    module_addr=%s"  % hex(module_addr))
        print("    base_addr=%s" % hex(base_addr))
        print("    channel_address=%s" % hex(channel_address))
        print("    addrN=%s" % hex(addrN))
        print("    TIMESTAMP=%s"    % is_timestamp)
        print("    FLAG=%s"         % is_flag)
        print("    MARKED=%s"       % is_marked)
        print("    BLOCKING=%s"     % is_blocking)
        print("    EVENT=%s"        % is_event)

    session.dma_write32(final_addr, wrdata)

    if verbose:
        print("    SI MODULE CONFIG")

        channels_m1 = [d.value for s,d in rsp_discovery if s == "channels"][0]
        if channel <= channels_m1:
            print("        channel=%d <= channels-1=%d" % (channel, channels_m1))
        else:
            print("        WARNING channel=%d > channels-1=%d" % (channel, channels_m1))

        #
        # enabled
        #
        rsp_enabled = session.send_get_msg_with_response(md,
            session.blank_us_ctrl_fields(md, "get_enabled"))[0].fields.items()
        module_enabled = [d.value for s,d in rsp_enabled if s == "module_enable"][0] != 0
        if module_enabled:
            print("        module enabled")
        else:
            print("        WARNING module disabled")

        #
        # event
        #
        if is_event:
            eventnum = wrdata & 0xFF
            event_select = 1 if eventnum > 128 else 0
            maskindex = eventnum - (128 if event_select else 0)
            rsp_event = session.send_get_msg_with_response(md,
                session.blank_us_ctrl_fields(md, "get_event", {"select": event_select}))[0].fields.items()
            event_mask = [d.value for s,d in rsp_event if s == "mask"][0]
            event_enabled = (event_mask & (1 << maskindex)) != 0
            if event_enabled:
                print("        event %d (from LSByte of wrdata) enabled" % eventnum)
            else:
                print("        WARNING event %d (from LSByte of wrdata) disabled" % eventnum)

        #
        # power
        #
        rsp_power = session.send_get_msg_with_response(md,
            session.blank_us_ctrl_fields(md, "get_power"))[0].fields.items()
        clk_disable = [d.value for s,d in rsp_power if s == "clk_disable"][0] != 0
        if clk_disable:
            print("        internal clock gating enabled")
        else:
            print("        WARNING internal clock gating disabled")

        #
        # sinst
        #
        rsp_sinst = session.send_get_msg_with_response(md,
            session.blank_us_ctrl_fields(md, "get_sinst"))[0].fields.items()
        sys_flow = [d.value for s,d in rsp_sinst if s == "sys_flow"][0]
        inst_flow = [d.value for s,d in rsp_sinst if s == "inst_flow"][0]
        non_blocking_throttle_level = [d.value for s,d in rsp_sinst if s == "non_blocking_throttle_level"][0]
        blocking_throttle_level = [d.value for s,d in rsp_sinst if s == "blocking_throttle_level"][0]
        sys_timestamp = [d.value for s,d in rsp_sinst if s == "sys_timestamp"][0]
        inst_timestamp_override = [d.value for s,d in rsp_sinst if s == "inst_timestamp_override"][0]

        enable_event = [d.value for s,d in rsp_sinst if s == "enable_event"][0]
        disable_event = [d.value for s,d in rsp_sinst if s == "disable_event"][0]
        enable_event_control = [d.value for s,d in rsp_sinst if s == "enable_event_control"][0] != 0
        disable_event_control = [d.value for s,d in rsp_sinst if s == "disable_event_control"][0] != 0
        if enable_event_control:
            print("        WARNING module_enable enabled by event %d" % enable_event)
        if disable_event_control:
            print("        WARNING module_enable disabled by event %d" % disable_event)

        mst_id_capture_en = [d.value for s,d in rsp_sinst if s == "mst_id_capture_en"][0]
        mst_id_filter_lo = [d.value for s,d in rsp_sinst if s == "mst_id_filter_lo"][0]
        mst_id_filter_hi = [d.value for s,d in rsp_sinst if s == "mst_id_filter_hi"][0]
        axis_id_width_p = [d.value for s,d in rsp_discovery if s == "axi_id"][0] + 1
        max_id = 2**axis_id_width_p - 1
        if mst_id_filter_lo != 0 or  mst_id_filter_hi != max_id:
            print("        WARNING (mst_id_filter_lo, mst_id_filter_hi)=(%d, %d)"
                  " but max range is (0, %d)" % (mst_id_filter_lo, mst_id_filter_hi, max_id))

        tx_timeout = [d.value for s,d in rsp_sinst if s == "tx_timeout"][0]
        if tx_timeout != 0:
            print("        WARNING tx_timeout=%d so blocking messages may time out" % tx_timeout)

        #
        # sinst_enables
        #
        group, chnumber = divmod(channel, 32)
        rsp_sinst_enables = session.send_get_msg_with_response(md,
            session.blank_us_ctrl_fields(md, "get_sinst_enables", {"group_index": group}))[0].fields.items()
        enable_map = [d.value for s,d in rsp_sinst_enables if s == "enable_map"][0]
        channel_enabled = (enable_map & (1 << chnumber)) != 0
        if channel_enabled:
            print("        channel %d in group %d at chnumber %d enabled" % (channel, group, chnumber))
        else:
            print("        WARNING channel %d in group %d at chnumber %d disabled" % (channel, group, chnumber))

# }}} def write_si_mailbox

def si_set_sinst(session=s, # {{{
    md="si1",
    sys_flow=0,
    inst_flow=0,
    non_blocking_throttle_level="never",
    blocking_throttle_level="never",
    sys_timestamp=1,
    inst_timestamp_override=0,
    enable_event=0,
    disable_event=0,
    enable_event_control=0,
    disable_event_control=0,
    mst_id_capture_en=1,
    mst_id_filter_lo=0,
    mst_id_filter_hi=-1,
    tx_timeout=0):

    fields = {"control_code": "set_sinst",
              "sys_flow": sys_flow,
              "inst_flow": inst_flow,
              "non_blocking_throttle_level": non_blocking_throttle_level,
              "blocking_throttle_level": blocking_throttle_level,
              "sys_timestamp": sys_timestamp,
              "inst_timestamp_override": inst_timestamp_override,
              "enable_event": enable_event,
              "disable_event": disable_event,
              "enable_event_control": enable_event_control,
              "disable_event_control": disable_event_control,
              "mst_id_capture_en": mst_id_capture_en,
              "mst_id_filter_lo": mst_id_filter_lo,
              "mst_id_filter_hi": mst_id_filter_hi,
              "tx_timeout": tx_timeout}

    session.mstream.send_msg(md, "system_control", fields)

    rsp = session.send_get_msg_with_response(md, s.blank_us_ctrl_fields(md, "get_sinst"))

    return rsp
# }}} def si_set_sinst

def si_set_enabled(session=s, # {{{
    md="si1",
    operation="apply",
    module_enable=1):

    fields = {"control_code": "set_enabled",
              "operation": operation,
              "module_enable": module_enable}

    session.mstream.send_msg(md, "system_control", fields)

    rsp = session.send_get_msg_with_response(md, s.blank_us_ctrl_fields(md, "get_enabled"))

    return rsp
# }}} def si_set_enabled

def si_set_sinst_enables(session=s, # {{{
    md="si1",
    operation="apply",
    group_index=0,
    enable_map=(2**32-1)):

    fields = {"control_code": "set_sinst_enables",
              "operation": operation,
              "group_index": group_index,
              "enable_map": enable_map}

    session.mstream.send_msg(md, "system_control", fields)

    rsp = session.send_get_msg_with_response(md, s.blank_us_ctrl_fields(md, "get_sinst_enables"))

    return rsp
# }}} def si_set_sinst_enables

def si_set_event(session=s, # {{{
    md="si1",
    operation="apply",
    select=0,
    mask=(2**128-1)):

    fields = {"control_code": "set_event",
              "operation": operation,
              "select": select,
              "mask": mask}

    session.mstream.send_msg(md, "system_control", fields)

    rsp = session.send_get_msg_with_response(md, s.blank_us_ctrl_fields(md, "get_event", {"select": select}))

    return rsp
# }}} def si_set_event

def me_set_enabled(session=s, # {{{
    md="rme1",
    operation="apply",
    upper_enable=(2**16-1),
    upper_ingress_enable=(2**16-1)):

    fields = {"control_code": "set_enabled",
              "operation": operation,
              "upper_enable": upper_enable,
              "upper_ingress_enable": upper_ingress_enable}

    session.mstream.send_msg(md, "system_control", fields)

    rsp = session.send_get_msg_with_response(md, s.blank_us_ctrl_fields(md, "get_enabled"))

    return rsp
# }}} def me_set_enabled

def me_set_event(session=s, # {{{
    md="rme1",
    operation="apply",
    pathgroup=0,
    pathway=0,
    overflow=0,
    select=0,
    mask=(2**128-1)):

    fields = {"control_code": "set_event",
              "operation": operation,
              "pathgroup": pathgroup,
              "pathway": pathway,
              "overflow": overflow,
              "select": select,
              "mask": mask}

    session.mstream.send_msg(md, "system_control", fields)

    rsp = session.send_get_msg_with_response(md, s.blank_us_ctrl_fields(md, "get_event", {"select": select}))

    return rsp
# }}} def me_set_event

def run_tinn(): # {{{

    print("Setting up UltraSoC infrastructure...", end='')

    # Enable Static Instrumentation module.
    si1_rsp_enabled = si_set_enabled(module_enable=0)
    si1_rsp_sinst = si_set_sinst()
    si1_rsp_event0 = si_set_event(select=0)
    si1_rsp_event1 = si_set_event(select=1)
    si1_rsp_sinst_enables = si_set_sinst_enables()
    si1_rsp_msg_params = get_msg("si1", "get_msg_params")

    # Enable Message Engine module.
    rme1_rsp_discovery = get_msg("rme1", "discovery_request")
    rme1_rsp_msg_params = get_msg("rme1", "get_msg_params")
    rme1_rsp_route = get_msg("rme1", "get_route")
    rme1_rsp_enabled = me_set_enabled(s)
    rme1_rsp_event0 = me_set_event(s, select=0)
    rme1_rsp_event1 = me_set_event(s, select=1)

    print("DONE")


    print("Copying semeion.data... ", end='')
    print("%d bytes DONE" %
          s.dma_write(tinn.ASCIIDATASET_ADDR, tinn.PATH_ASCIIDATASET))

    print("Copying ACPU binary... ", end='')
    print("%d bytes DONE" %
          s.dma_write(tinn._START_ACPU, tinn.PATH_ACPU_BIN))

    print("Copying SCPU binary... ", end='')
    print("%d bytes DONE" %
          s.dma_write(tinn._START_SCPU, tinn.PATH_SCPU_BIN))


    # Initialise magic IPC locations, as specified in tinn_taygete.h
    print("Initialising IPC locations... ", end='')
    s.dma_write32(tinn.HOSTFLAG_ACPU, 0)
    s.dma_write32(tinn.HOSTFLAG_SCPU, 0)
    s.dma_write32(tinn.TOSLV_CMD, 0)
    s.dma_write32(tinn.TOMST_REQ, 0)
    s.dma_write32(tinn.TOSLV_BUFFADDR, 0xdeadbeef)
    s.dma_write32(tinn.TOMST_BUFFADDR, 0xdeadbeef)
    print("DONE")

    print("Getting CPU handles...")
    acpu = s.get_jpam("ACPU", xlen=64, initialise=True)
    scpu = s.get_jpam("SCPU", xlen=64, initialise=True)
    print("DONE")

    print("Running CPUs...")
    acpu.hart_run()
    scpu.hart_run()
    print("DONE")


    print("Starting tinn... ", end='')

    try:
      vc_logfile = open("log.vc.txt", 'w')
    except:
      vc_logfile = sys.stdout

    try:
      si_logfile = open(tinn.PATH_SI_LOG, 'w')
    except:
      si_logfile = sys.stdout

    # Arbitrary time delay before start recording to reduce the amount of quite
    # boring data collected in training phase.
    time.sleep(120) # 2m0s

    # Enable SI now that sinst_data sink is available.
    si1_rsp_enabled = si_set_enabled(module_enable=1)

    print("DONE")


    # Print VC lines until some infers have been done, checking magic address.
    ts = time.time() # Time start
    tn = ts          # Time now (this loop iteration, initialization)
    while (s.dma_read32(tinn.HOSTFLAG_ACPU) < 200):
        tp = tn             # Time previous (previous loop iteration)
        tn = time.time()    # Time now (this loop iteration)
        if (tn - tp) < 1:   # Wait at least a second between iterations.
            time.sleep(1)
            tn = time.time()
            assert (tn - tp) >= 1
        tds = tn - ts       # Time difference since start

        proc_sinst(si_logfile)
        vc_readlines(vc_logfile)

        print("Running tinn... %fs" % tds, end='\r')
        sys.stdout.flush()

    print("Ran tinn for %fs" % tds)


    print("Stopping CPUs...")

    # Disable module to stop more messages flooding out.
    si_set_enabled(module_enable=0)

    try:
        acpu.hart_halt()
        scpu.hart_halt()
    except:
        pass

    print("DONE")


    print("Closing logfiles... ", end='')
    vc_readlines(vc_logfile)
    proc_sinst(si_logfile)
    vc_logfile.close()
    si_logfile.close()
    print("DONE")
# }}} def run_tinn

def si_logfile_to_vcd(): # {{{

    def reduce_time(t, factor=130):
        assert isinstance(t, int)
        ret = int(t / factor) * factor
        assert isinstance(ret, int)
        return ret

    print("Sorting SI logfile... ", end='')
    try:
        os.system("sort -n -o %s %s" % (tinn.PATH_SI_LOG, tinn.PATH_SI_LOG))
    except:
        pass
    print("DONE")

    print("Writing VCD header... ", end='')

    # Look at every line and find all unique data values keeping count of how
    # often each appears.
    # Also find list of all signals which change at the first time.
    dv_cnts = {}
    t0_dvs = []
    t0 = None
    with open(tinn.PATH_SI_LOG, 'r') as fd:
        for line in fd:
            t, c, d = line.split()[:3]
            dv = int(d, 16)
            dv_cnts[dv] = dv_cnts.setdefault(dv, 0) + 1

            tv = reduce_time(int(t))
            if t0 == None:
                t0 = tv
            if tv <= t0:
                t0_dvs.append(dv)
    assert 0 < len(dv_cnts)
    assert 0 < len(t0_dvs)
    assert isinstance(t0, int)

    # List of unique data values sorted by descending number of appearances.
    dvs = [vc[0] for vc in \
           sorted(dv_cnts.items(), key=lambda vc: vc[1], reverse=True)]

    def int2varid(x): # {{{
        assert type(x) is int
        assert x >= 0

        # Each variable is assigned an arbitrary, compact ASCII identifier for
        # use in the value change section. The identifier is composed of
        # printable ASCII characters from ! to ~ (decimal 33 to 126).
        numerals = ''.join(chr(i) for i in range(33, 127))
        base = len(numerals)

        if x == 0:
            return numerals[0]
        r = []
        while x:
            r.append(numerals[x % base])
            x //= base
        r.reverse()
        return ''.join(r)
    # }}}

    # Most frequently used data values have shorter varids.
    dv_varids = {dv: int2varid(i) for i,dv in enumerate(dvs)}

    # Use nm to generate {<dv>: <symbolname>}
    # NOTE: If using polymorphic functions --demangle will make them all look
    # like the same thing which may or may not be desirable.
    tool = "$RISCV/bin/riscv64-unknown-elf-nm --demangle --no-sort"
    symboltable = "tinn.symbols.txt"
    cmdfmt = tool + " %s >> " + symboltable
    # readelf could be used instead of nm
    # c++filt could be used instead of --demangle
    try:
        os.remove(symboltable)
    except:
        pass

    try:
        os.system(cmdfmt % tinn.PATH_ACPU_ELF)
        os.system(cmdfmt % tinn.PATH_SCPU_ELF)
    except:
        assert False, "Cannot create symboltable %s" % symboltable

    # For each address find the corresponding function name and use that as
    # signal name.
    dv_nms = {}
    with open(symboltable, 'r') as fd:
        for line in fd:
            # Line format for nm symbol table.
            # 000000006000c4d4 T abort
            # 00000000700014c8 t fprop(Tinn*, float const*)
            # 0000000070014f88 r initDataSet(DataItem*)::__PRETTY_FUNCTION__
            # 0000000070003096 T std::type_info::~type_info()
            d, _t, n = line.split()[:3]
            dv = int(d, 16)

            # Only extract names for recorded data values.
            if dv not in dvs: continue

            if 0x60000000 <= dv <= 0x6fffffff:
                sec = "acpu."
            elif 0x70000000 <= dv <= 0x7fffffff:
                sec = "scpu."
            else:
                sec = "misc."

            # Remove function arg types from demangled name.
            # Replace non-alphanum characters with underscores.
            nm = ''.join(c if c.isalnum() else '_' for c in n.split('(')[0])

            dv_nms[dv] = sec + nm

    # Assign names to any remaining data values.
    # NOTE: If everything is working as expected then this loop will do nothing.
    # If you're getting lots on unknown names then the ELF may be out of date or
    # something else has gone wrong with the risvc tool.
    for dv in dvs:
        if dv not in dv_nms.keys():
            dv_nms[dv] = "unknown." + hex(dv)

    with open(tinn.PATH_SI_VCD, 'w') as fd:
        put = fd.write
        put("$comment UltraSoC Taygete ZC706 platform running Tinn $end\n")
        put("$date %s $end\n" % str(time.ctime()))
        put("$timescale 1s $end\n")
        put("$scope module tinn $end\n")
        for dv in dvs:
            nm = dv_nms[dv]
            varid = dv_varids[dv]
            put("$var wire 1 %s %s $end\n" % (dv_varids[dv], dv_nms[dv]))
        put("$upscope $end\n")
        put("$enddefinitions $end\n")

    print("DONE")

    print("Writing VCD body... ", end='')

    # For each line use dict of varids keyed by addresses to append time and
    # change to VCD body. ch0->0 (exit), ch1->1 (enter)
    with open(tinn.PATH_SI_LOG, 'r') as fd_log, \
         open(tinn.PATH_SI_VCD, 'a') as fd_vcd:
        put = fd_vcd.write

        # Zero-initialize all signals.
        # NOTE: This will cause some misrepresentation for any signals which
        # were actually non-zero at the beginning of recording.
        put("#%d\n" % t0)
        for dv in dvs:
            if dv not in t0_dvs:
                varid = dv_varids[dv]
                put("b0 %s\n" % varid)

        for line in fd_log:
            t, c, d = line.split()[:3]

            tv = reduce_time(int(t))
            put("#%d\n" % tv)

            dv = int(d, 16)
            varid = dv_varids[dv]

            if c == '0': cv = '0'
            elif c == '1': cv = '1'
            else: cv = 'x'

            put("b%s %s\n" % (cv, varid))

    print("DONE")

# }}} def si_logfile_to_vcd

#run_tinn()
si_logfile_to_vcd()

#print("""
#=== Interactive target session ===
#  Use created session object. Example use:
#    s.dma_read32(<address>)            <- Read 32-bit word/register (via DMA)
#    s.dma_write32(<address>,<value>)   <- Write 32-bit word/register (via DMA)
#    s.dma_write(<address>,<filename>)  <- Write file to memory (via DMA)
#    s.load_and_run_riscv(<binfile>,<CPU>)
#                                       <- Load binary file to memory and run RISC-V hooked up to CPU
#    s.run_riscv_app(<app_name>)        <- Load and run binary files on all CPUs, <app_name> can be one of:
#                                                  {0}
#    s.handle_vc()                      <- Read data from console and dump it to screen
#    scpu.read_gpc("sp")     <- Read stack pointer (GPR)
#    scpu.read_dpc()         <- Read PC
#    scpu.read_csr("mcause") <- Read mcause (CSR)
#""".format(("\n" + " "*50).join(['"'+app+'"' for app in .find_all_binapps()])))

