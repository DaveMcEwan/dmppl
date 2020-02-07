#!/usr/bin/env python

from __future__ import print_function
import sys
import itertools
from copy import deepcopy

version_help = "Python 2.7 or 3.4+ required."
if sys.version_info[0] == 2:
    assert sys.version_info[1] == 7, version_help
elif sys.version_info[0] == 3:
    assert sys.version_info[1] >= 4, version_help
else:
    assert False, version_help

from math import *
golden = (1 + 5**0.5) / 2

# {{{ utility functions

def clog(x, base):
    assert type(x) is int
    assert x > 0
    assert type(base) is int
    assert base > 1

    return int(ceil(log(x,base)))

def flog(x, base):
    assert type(x) is int
    assert x > 0
    assert type(base) is int
    assert base > 1

    return int(floor(log(x,base)))

def int2base(x, base):
    assert type(x) is int
    assert x >= 0
    assert type(base) is int
    assert base > 1

    numerals = '0123456789abcdefghijklmnopqrstuvwxyz'

    if x == 0:
        return numerals[0]
    r = []
    while x:
        r.append(numerals[x % base])
        x /= base
    r.reverse()
    return ''.join(r)

# }}} utility functions

# {{{ mappings
# Mappings are from leafnode index to function index.

def map_fwd(i, width, b):
    return i

def map_pingpong(i, width, b):
    n = b**width
    return i*2 if (i < n/2.0) else 2*(n-i)-1

def map_pongping(i, width, b):
    return int(b**width-((i+1)/2)) if (i % 2) else int(i/2)

def map_strideb(i, width, b):
    n = b**width
    return ((i*b) % n) + int((i*b) / n)

def map_strodeb(i, width, b):
    n = b**width
    return (int((i*n) / b) % n) + int(i/b)

def map_basebrev(i, width, b):
    d = int2base(i, b)                      # Represent in base b str from int.
    z = ('0'*(width - len(d)) + d)[::-1]    # Zero fill and reverse.
    return int(z, b)                        # Re-interpret int from base b str.

def map_grayfwd(i, width, b):
    r = 0
    for k in range(width):
        j = int(i/(b**k))
        d = (j-int(j/b)) % b
        r += d * b**k
    return r

def map_grayrev(i, width, b):
    r = 0
    for k in range(width):
        j = int(i/(b**k))
        d = (j-int(j/b)) % b
        r += d * b**(width-k-1)
    return r

available_mappings = [
    (map_fwd,       'FWD'),
    (map_basebrev,  'BASEBREV'),
    (map_pingpong,  'PINGPONG'),
    (map_pongping,  'PONGPING'),
    (map_strideb,   'STRIDEB'),
    (map_strodeb,   'STRODEB'),
    (map_grayfwd,   'GRAYFWD'),
    (map_grayrev,   'GRAYREV'),
]

# These base2 functions are elegant so kept for reference.
def map_binrev(i, width, b=0): # b is fixed at 2
    r = 0
    j = 0
    while (j < width):
        r |= ((i >> j) & 1) << (width - j - 1)
        j += 1
    return r

def map_bingrayfwd(i, width, b=0): # b is fixed at 2
    return (i ^ (i >> 1))

def map_bingrayrev(i, width, b=0): # b is fixed at 2
    r = 0
    j = 0
    while (j < width):
        r |= (((i ^ (i >> 1)) >> j) & 1) << (width - j - 1)
        j += 1
    return r

def map_alt_grayfwd(i, width, b):
    n = b**width
    gb = b**2

    numerals = '0123456789abcdefghijklmnopqrstuvwxyz'
    gnumerals = ''.join([numerals[(j-int(j/b)) % b] for j in range(gb)])

    if i == 0:
        return 0
    r = []
    while i > 0:
        r.append(gnumerals[i % gb])
        i /= b
    r += numerals[0]*(width-len(r))
    r.reverse()
    r = ''.join(r)
    return int(r, b)

def map_alt_grayrev(i, width, b):
    n = b**width
    gb = b**2

    numerals = '0123456789abcdefghijklmnopqrstuvwxyz'
    gnumerals = ''.join([numerals[(j-int(j/b)) % b] for j in range(gb)])

    if i == 0:
        return 0
    r = []
    while i > 0:
        r.append(gnumerals[i % gb])
        i /= b
    r += numerals[0]*(width-len(r))
    #r.reverse()
    r = ''.join(r)
    return int(r, b)


def print_maps(N_INs, bases, mappings, fd):
    for w in N_INs:
        for b in bases:
            n = clog(w, b)
            print("Maps for b=%d, w=%d." % (b, w), file=fd)
            fmt = " | ".join(['{:^9}' for m in mappings])
            head_line = [nm for fn, nm in mappings]
            print(fmt.format(*head_line), file=fd)
            print(fmt.format(*['-'*9 for m in mappings]), file=fd)
            for i in range(0, w):
                data_line = [str(fn(i, n, b)) for fn, nm in mappings]
                print(fmt.format(*data_line), file=fd)
            print('', file=fd)
# }}} mappings

def calculate_ops(b, w, fn): # {{{
    '''Return a list of operations with the index of the output wire (or None),
       and the indices (or None) of the input wires.
       If all input wires are None then the operation can be removed.
    '''

    n = b**clog(w, b)
    n_levels = clog(w, b)
    n_ops = int('1'*(n_levels), b) # basic tree
    n_wires = int('1'*(n_levels+1), b) # basic tree

    # Ops are numbered o with root node (bottom of tree) having the number 0.
    # outwires are numbered the same as their respective ops.
    # inwires are numbered as o*b+1..o*b+1+b
    # This definition can be used to generate basic tree for verilog etc.
    opnum_root = 0
    opnum_leafmax = n_ops - 1
    opnum_leafmin = opnum_leafmax / b

    # Calculate reduced tree connections.
    # Each op is (int/None outwire, [ints/Nones inwires])
    ops = [None for o in range(n_ops)]
    for o in range(n_ops)[::-1]:
        basic_inwires = range(o*b+1, o*b+1+b)
        if o >= opnum_leafmin:
            inwires = [i if fn(i-n_ops, n_levels, b) < w else None \
                            for i in basic_inwires]
        else:
            inwires = [ops[i][0] for i in basic_inwires]

        connected = [0 if (i is None) else 1 for i in inwires]
        n_connected = sum(connected)

        if n_connected == 0:
            outwire = None
        elif n_connected == 1:
            idx = connected.index(1)
            outwire = inwires[idx] # Connect lone wire through.
            inwires[idx] = None    # and disconnect op above.
        else:
            outwire = o

        # Note that since inwires may have changed a recalculation of
        # n_connected might yield a different answer.

        ops[o] = (outwire, tuple(inwires))

    return tuple(ops)
# }}} calculate_ops

def calculate_opsizes(ops, b, a): # {{{
    '''Take a list of operations with the index of the output wire (or None),
       Return the size/cost/delay/capacitance associated with each operation
       as a list, for a particular value of alpha.
    '''
    # Get the number of connected inwires for each operation as a list.
    opins = [sum([0 if inwire is None else 1 for inwire in o[1]]) \
            for o in ops]
    #print(opins)
    ret = []
    for o in opins:
        unoptimisable = int(o > 1)
        fixalpha = a * unoptimisable
        c = unoptimisable * (o/float(b))**fixalpha
        ret.append(c)

    return ret
# }}} calculate_opsizes

def calculate_oppaths(b, w, fn): # {{{
    '''Take the base and width of inputs.
       Return the indices of the operations associated with each input.
       Paths are stored from leaf to root.
    '''
    n = b**clog(w, b)
    n_levels = clog(w, b)

    mapins = tuple(fn(i, n_levels, b) for i in range(n))
    #print(mapins)
    usedins = tuple(i for i,j in enumerate(mapins) if j < w)
    #print(usedins)

    oppaths = tuple([ int(i/b**(l+1)) + int('0'+'1'*(n_levels-l-1), b) \
            for l in range(n_levels) ] \
                for i in usedins)
    #print(oppaths)

    #assert len(oppaths) == w
    #for p in oppaths:
    #    assert len(tuple(p)) == n_levels
    return oppaths
# }}} calculate_oppaths

def calculate_t(oppaths, opsizes): # {{{

    t_per_leafnode = [sum([opsizes[op] for op in p]) for p in oppaths]
    #print(t_per_leafnode)
    t = sum(t_per_leafnode)

    return t
# }}} calculate_t

def calculate_results(bases, N_INs, mappings, alphas): # {{{
    from joblib import Parallel, delayed

    print("Initializing results structure...")
    # Key order is always b,w,nm,a,
    # Always store as dicts rather than lists to ease merging in large runs.
    results = {}
    for b in bases:
        results[b] = {}
        for w in N_INs:
            n = b**clog(w, b) # Round up w to next power of b.
            p = b**flog(w, b) # Round down w to previous power of b.
            depth = clog(w, b) # Depth of op tree, #levels.

            # Total number of operations in tree.
            # These will be optimised away for non Power-Of-b values of w.
            # http://mathworld.wolfram.com/Rule50.html
            if depth > 1:
                o_max = (b**depth - 1) / (b - 1)
            else:
                o_max = 1
            o_min = (w-2)/(b-1) + 1 # Number of unoptimisable operations.
            assert o_min <= o_max, "o_min=%d, o_max=%d" % (o_min, o_max)

            # t for maximally unbalanced.
            t_max = int((w * (w+1) * 0.5)-1)

            # t for maximally balanced (approx).
            t_bal = w*log(w, b)

            #n_floor = 2*p-w # base2 only.
            n_floor = p-ceil(float(w-p)/float(b-1))
            n_ceil = w - n_floor
            # t for balanced (exact integer).
            t_min = int(n_floor*flog(w, b) + n_ceil*clog(w, b))

            results[b][w] = {
                "n": n,
                "p": p,
                "depth": depth,
                "o_max": o_max,
                "o_min": o_min,
                "t_max": t_max,
                "t_bal": t_bal,
                "t_min": t_min,
            }
            for fn, nm in mappings:
                results[b][w][nm] = {
                    't': {},
                    'u': {},
                }

    # Temporary result structures.
    tmp_ops = {b: {w: {} \
        for w in N_INs} \
            for b in bases}
    tmp_oppaths = {b: {w: {} \
        for w in N_INs} \
            for b in bases}
    tmp_opsizes = {b: {w: {nm: {} \
        for fn,nm in mappings} \
            for w in N_INs} \
                for b in bases}

    # Fill in ops and oppaths
    print("Calculating ops... over cross of (b,w,mapping)")
    cpi_bwm = tuple(itertools.product(bases, N_INs, [m for m in mappings]))
    cpo_ops = Parallel(n_jobs=-2) \
        (delayed(calculate_ops)(b, w, fn) \
            for (b, w, (fn, nm)) in cpi_bwm)
    print("Storing ops to tmp structures...")
    for i, (b, w, (fn, nm)) in enumerate(cpi_bwm):
        tmp_ops[b][w][nm] = cpo_ops[i]
    print("Calculating oppaths... over cross of (b,w,mapping)")
    cpo_oppaths = Parallel(n_jobs=-2) \
        (delayed(calculate_oppaths)(b, w, fn) \
            for (b, w, (fn, nm)) in cpi_bwm)
    print("Storing oppaths to tmp structures...")
    for i, (b, w, (fn, nm)) in enumerate(cpi_bwm):
        tmp_oppaths[b][w][nm] = cpo_oppaths[i]

    # Fill in opsizes, depends on tmp_ops
    if 2 in bases:
        print("Calculating opsizes (b==2)... over cross of (w,mapping)")
        cpi_wm = tuple(itertools.product(N_INs, [m for m in mappings]))
        cpo_opsizes2 = Parallel(n_jobs=-2) \
            (delayed(calculate_opsizes)(tmp_ops[2][w][nm], 2, 0.0) \
                for (w, (fn, nm)) in cpi_wm)
        print("Storing opsizes to tmp structure (b==2)...")
        for i, (w, (fn, nm)) in enumerate(cpi_wm):
            tmp_opsizes[2][w][nm] = cpo_opsizes2[i]

    non2_bases = [b for b in bases if b != 2]
    cpi_bwma = tuple(itertools.product(non2_bases, N_INs,
                                       [m for m in mappings], alphas))
    if len(non2_bases) != 0:
        print("Calculating opsizes (b!=2)... over cross of (b,w,mapping,a)")
        cpo_opsizes = Parallel(n_jobs=-2) \
            (delayed(calculate_opsizes)(tmp_ops[b][w][nm], b, a) \
                for (b, w, (fn, nm), a) in cpi_bwma)
        print("Storing opsizes to tmp structure (b!=2)...")
        for i, (b, w, (fn, nm), a) in enumerate(cpi_bwma):
            tmp_opsizes[b][w][nm][a] = cpo_opsizes[i]

    # Fill in t, depends on tmp_oppaths, tmp_opsizes
    if 2 in bases:
        print("Calculating t (b==2)... over cross of (w,mapping)")
        cpo_t2 = Parallel(n_jobs=-2) \
            (delayed(calculate_t)(tmp_oppaths[2][w][nm],
                                      tmp_opsizes[2][w][nm]) \
                for (w, (fn, nm)) in cpi_wm)
        print("Storing t to results structure (b==2)...")
        for i, (w, (fn, nm)) in enumerate(cpi_wm):
            results[2][w][nm]["t"] = cpo_t2[i]
    if len(non2_bases) != 0:
        print("Calculating t (b!=2)... over cross of (b,w,mapping,a)")
        cpo_t = Parallel(n_jobs=-2) \
            (delayed(calculate_t)(tmp_oppaths[b][w][nm],
                                      tmp_opsizes[b][w][nm][a]) \
                for (b, w, (fn, nm), a) in cpi_bwma)
        print("Storing t to results structure...")
        for i, (b, w, (fn, nm), a) in enumerate(cpi_bwma):
            results[b][w][nm]["t"][a] = cpo_t[i]


    # Derive further results.
    # This is serial but could be parallel, overhead permitting.
    print("Calculating u...")
    for b in bases:
        for w in N_INs:
            for fn, nm in mappings:
                if b == 2:
                    t     = results[2][w][nm   ]["t"]
                    t_fwd = results[2][w]["FWD"]["t"]
                    t_min = results[2][w]["t_min"]
                    u = w - w * float(t) / float(t_fwd)
                    v = w - w * float(t) / float(t_min)
                    results[2][w][nm]["u"] = u
                    results[2][w][nm]["v"] = v
                else:
                    for a in alphas:
                        t     = results[b][w][nm   ]["t"][a]
                        t_fwd = results[b][w]["FWD"]["t"][a]
                        u = w - w * float(t) / float(t_fwd)
                        results[b][w][nm]["u"][a] = u

    print("Calculating u_diff...")
    for b in bases:
        for w in N_INs:
            if b == 2:
                u_values = [results[2][w][nm]["u"] for fn, nm in mappings]
                u_hi = max(u_values)
                u_lo = min(u_values)
                u_diff = u_hi - u_lo
                results[2][w]["u_hi"] = u_hi
                results[2][w]["u_lo"] = u_lo
                results[2][w]["u_diff"] = u_diff
            else:
                results[b][w]["u_hi"] = {}
                results[b][w]["u_lo"] = {}
                results[b][w]["u_diff"] = {}
                for a in alphas:
                    u_values = [results[b][w][nm]["u"][a] for fn, nm in mappings]
                    u_hi = max(u_values)
                    u_lo = min(u_values)
                    u_diff = u_hi - u_lo
                    results[b][w]["u_hi"][a] = u_hi
                    results[b][w]["u_lo"][a] = u_lo
                    results[b][w]["u_diff"][a] = u_diff

    print("Returning results...")
    return results

# }}} calculate_results

def dump_results(results, fd): # {{{
    import yaml
    yaml.safe_dump(results, fd)
    return
# }}} dump_results

def load_results(fd): # {{{
    import yaml
    results = yaml.safe_load(fd)
    return results
# }}} load_results

def print_tables(alphas, N_INs, bases, mappings, fd, results): # {{{
    for a in alphas:
        for b in bases:

            table_headers = [
                "w",
                "depth",
                "o_max",
                "o_min",
                "t_bal",
                "t_min",
                "t_max",
            ]
            map_header_fmt = "{:43}"
            table_data_fmt = ' '.join([
                '{:^5}',     # w
                '{:^5}',     # depth
                '{:^5}',     # o_max
                '{:^5}',     # o_min
                '{:^7.3f}',  # t_bal
                '{:^5}',     # t_min
                '{:^5}',     # t_max
            ])
            table_header_fmt = ' '.join([
                '{:5}', # w
                '{:5}', # depth
                '{:5}', # o_max
                '{:5}', # o_min
                '{:7}', # t_bal
                '{:5}', # t_min
                '{:5}', # t_max
            ])

            mapping_headers = ["b=%d,alpha=%0.3f" % (b, a)]
            data_w = 9
            for fn, nm in mappings:
                table_headers.append("t")
                table_headers.append("u")
                map_header_fmt += " | {:%d}" % (2*data_w + 1)
                table_header_fmt += " | {:%d} {:%d}" % (data_w, data_w)
                table_data_fmt += " | {:^%d.3f} {:^%d.3f}" % (data_w, data_w)
                mapping_headers.append(nm)

            table_data = []
            for w in N_INs:
                table_data_line = [
                    w,
                    results[b][w]["depth"],
                    results[b][w]["o_max"],
                    results[b][w]["o_min"],
                    results[b][w]["t_bal"],
                    results[b][w]["t_min"],
                    results[b][w]["t_max"],
                ]
                for fn, nm in mappings:
                    if b==2:
                        table_data_line.append(results[b][w][nm]["t"])
                        table_data_line.append(results[b][w][nm]["u"])
                    else:
                        table_data_line.append(results[b][w][nm]["t"][a])
                        table_data_line.append(results[b][w][nm]["u"][a])
                table_data.append(table_data_line)

            print('', file=fd)
            print(map_header_fmt.format(*mapping_headers), file=fd)
            print(table_header_fmt.format(*table_headers), file=fd)
            print(table_header_fmt.format(*[
                '-'*5,  # w
                '-'*5, # depth
                '-'*5, # o_max
                '-'*5, # o_min
                '-'*7, # t_bal
                '-'*5, # t_min
                '-'*5, # t_max
                '-'*9, '-'*9, # t/u0 FWD
                '-'*9, '-'*9, # t/u1 BASEBREV
                '-'*9, '-'*9, # t/u2 PINGPONG
                '-'*9, '-'*9, # t/u3 PONGPING
                '-'*9, '-'*9, # t/u4 STRIDEB
                '-'*9, '-'*9, # t/u5 STRODEB
                '-'*9, '-'*9, # t/u6 GRAYFWD
                '-'*9, '-'*9, # t/u7 GRAYREV
            ]), file=fd)
            for line in table_data:
                print(table_data_fmt.format(*line), file=fd)

# }}} print_tables

def plot_graphs(alphas, N_INs, bases, mappings, results,
                interactive=False, png=False, svg=False): # {{{

    markers = [
        '-ob',  # solid line, circle marker, blue
        '-sg',  # solid line, square marker, green
        '-xr',  # solid line, x marker, red
        '-dc',  # solid line, thin_diamond marker, cyan
        '-*m',  # solid line, star, magenta
        '-hy',  # solid line, hexagon1 marker, yellow
        '-+k',  # solid line, plus marker, black
        '-+b',  # solid line, plus marker, blue
        '-1g',  # solid line, plus marker, green
    ]

    import matplotlib.pyplot as plt

    for a in alphas:
        for b in bases:
            title = "b=%d,alpha=%0.3f" % (b, a)
            filename = "img/%s" % title.replace('.', '_')

            f = plt.figure(dpi=96, figsize=(16,9))
            f.canvas.set_window_title(title)
            plt.title(title)
            plt.grid(True)
            plt.xticks([w for w in N_INs if w % 8 == 0])
            plt.xlim(min(N_INs)-1, max(N_INs)+1)
            plt.xlabel("w")
            plt.ylabel("u")

            for map_i, (fn, nm) in enumerate(mappings):
                if nm == "FWD":
                    continue
                if b == 2:
                    u = [results[b][w][nm]['u'] for w in N_INs]
                else:
                    u = [results[b][w][nm]['u'][a] for w in N_INs]
                plt.plot(N_INs, u, markers[map_i], label=nm)

            #plt.ylim(ymin=0.0)
            #plt.yscale("log")
            #plt.yscale("symlog", linthreshy=1.0)
            #plt.yscale("logit")
            plt.legend(loc=2)
            plt.tight_layout()

            if png:
                plt.savefig("%s.png" % filename)
            if svg:
                plt.savefig("%s.svg" % filename)

    for a in alphas:
        title = "u_diff,alpha=%0.3f" % a
        filename = "img/%s" % title.replace('.', '_')

        f = plt.figure(dpi=96, figsize=(16,9))
        f.canvas.set_window_title(title)
        plt.title(title)
        plt.grid(True)
        plt.xticks([w for w in N_INs if w % 8 == 0])
        plt.xlim(min(N_INs)-1, max(N_INs)+1)
        plt.xlabel("w")
        plt.ylabel("u")
        for base_i, b in enumerate(bases):
            if b == 2:
                u_diff = [results[b][w]['u_diff'] for w in N_INs]
            else:
                u_diff = [results[b][w]['u_diff'][a] for w in N_INs]
            plt.plot(N_INs, u_diff, markers[base_i], label="b=%d" % b)
        plt.legend(loc=2)
        plt.tight_layout()

        if png:
            plt.savefig("%s.png" % filename)
        if svg:
            plt.savefig("%s.svg" % filename)

    if 2 in bases: # {{{
        title = "b=2"
        filename = "img/%s" % title

        f = plt.figure(dpi=96, figsize=(16,9))
        f.canvas.set_window_title(title)
        plt.title(title)
        plt.grid(True)
        plt.xticks([w for w in N_INs if w % 8 == 0])
        plt.xlim(min(N_INs)-1, max(N_INs)+1)
        plt.xlabel("w")
        plt.ylabel("v")

        for map_i, (fn, nm) in enumerate(mappings):
            v = [results[2][w][nm]['v'] for w in N_INs]
            plt.plot(N_INs, v, markers[map_i], label=nm)

        #plt.ylim(ymin=0.0)
        #plt.yscale("log")
        #plt.yscale("symlog", linthreshy=1.0)
        #plt.yscale("logit")
        plt.legend(loc=2)
        plt.tight_layout()

        if png:
            plt.savefig("%s.png" % filename)
        if svg:
            plt.savefig("%s.svg" % filename)
    # }}} 2 in bases

    if interactive:
        plt.show()

# }}} plot_graphs

def plot_alpha3d(alphas, N_INs, bases, mappings, results,
                interactive=False, png=False): # {{{
# TODO: This is unusable. Use mayavi instead.

    markers = [
        '-ob',  # solid line, circle marker, blue
        '-sg',  # solid line, square marker, green
        '-xr',  # solid line, x marker, red
        '-dc',  # solid line, thin_diamond marker, cyan
        '-*m',  # solid line, star, magenta
        '-hy',  # solid line, hexagon1 marker, yellow
        '-+k',  # solid line, plus marker, black
    ]

    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import numpy as np

    def z_pt(b, nm, a, w):
        w_index = N_INs.index(w)
        if nm in algos:
            return results[b][nm][a]["u"][w_index]
        else:
            return results[b][nm][w_index]

    for b in bases:
        title = "b=%d" % b
        filename = "img/%s" % title

        f = plt.figure(dpi=96, figsize=(16,9))
        f.canvas.set_window_title(title)
        ax = f.gca(projection='3d')

        X, Y = np.meshgrid(N_INs, alphas)
        Z = {}

        plt.title(title)
        plt.grid(True)
        plt.xticks([w for w in N_INs if w % 8 == 0])
        plt.xlim(min(N_INs)-1, max(N_INs)+1)
        plt.xlabel("w")
        plt.ylabel("a")
        ax.set_zlabel("u")

        # TODO: matplotlib doesn't overlap surfaces.
        for map_i, (fn, nm) in enumerate(mappings):
            Z[nm] = np.array([z_pt(b, nm, a, w) \
                for w,a in zip(np.ravel(X), np.ravel(Y))]).reshape(X.shape)
            ax.plot_surface(X, Y, Z[nm], label=nm)

        plt.ylim(ymin=0.0)
        #plt.yscale("log")
        #plt.yscale("symlog", linthreshy=1.0)
        #plt.yscale("logit")
        #plt.legend()
        plt.tight_layout()

        #if png:
        #    plt.savefig("%s.png" % filename)
    if interactive:
        plt.show()

# }}} plot_alpha3d

if __name__ == "__main__": # {{{
    import argparse

    parser = argparse.ArgumentParser(
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("-o", "--outfile",
                        type=argparse.FileType('w'),
                        default=sys.stdout,
                        help="Output file for STDOUT.")

    parser.add_argument("-l", "--load",
                        type=argparse.FileType('r'),
                        default=None,
                        help="File containing pre-computed results.")

    parser.add_argument("-d", "--dump",
                        default=False,
                        action='store_true',
                        help="Dump results in YAML format to outfile.")

    parser.add_argument("-z", "--algorithms",
                        type=str,
                        default=','.join([nm for fn, nm in available_mappings]),
                        help="Port-mapping algorithms to use, comma separated.")

    parser.add_argument("-m", "--maps",
                        default=False,
                        action='store_true',
                        help="Print mapping tables to outfile.")

    parser.add_argument("-t", "--tables",
                        default=False,
                        action='store_true',
                        help="Print result tables to outfile.")

    parser.add_argument("-i", "--interactive",
                        default=False,
                        action='store_true',
                        help="Show interactive plot figures.")

    parser.add_argument("-p", "--png",
                        default=False,
                        action='store_true',
                        help="Save PNG figures.")

    parser.add_argument("-s", "--svg",
                        default=False,
                        action='store_true',
                        help="Save SVG figures.")

    parser.add_argument("-b", "--base",
                        type=int,
                        default=0,
                        help="Base for calculations. 0 means [bmin..bmax].")

    parser.add_argument("--bmin",
                        type=int,
                        default=2,
                        help="Minimum base for calculations.")

    parser.add_argument("--bmax",
                        type=int,
                        default=5,
                        help="Maximum base for calculations.")

    parser.add_argument("--wmin",
                        type=int,
                        default=2,
                        help="Minimum width for calculations.")

    parser.add_argument("--wmax",
                        type=int,
                        default=20,
                        help="Maximum width for calculations.")

    parser.add_argument("-w", "--width",
                        type=int,
                        default=0,
                        help="Use only one width. 0 means [wmin..wmax]")

    parser.add_argument("-a", "--alpha",
                        type=float,
                        default=golden,
                        help="Non-linear operation size constant.")

    parser.add_argument("--alpha3d",
                        default=False,
                        action='store_true',
                        help="3D plot over range of alphas.")

    parser.add_argument("--amin",
                        type=float,
                        default=0.0,
                        help="Minimum alpha for surface plot. Use --alpha3d")

    parser.add_argument("--amax",
                        type=float,
                        default=5,
                        help="Maximum alpha for surface plot. Use --alpha3d")

    parser.add_argument("--alen",
                        type=int,
                        default=20,
                        help="Number of alpha values. Use --alpha3d")

    args = parser.parse_args()

    N_INs = [args.width] if args.width != 0 else range(args.wmin, args.wmax+1)
    bases = [args.base] if args.base != 0 else range(args.bmin, args.bmax+1)
    algos = [a.upper() for a in args.algorithms.split(',')]
    if "FWD" not in algos:
        algos.append("FWD")
    mappings = [m for m in available_mappings if m[1] in algos]

    alphas = [args.alpha]
    if args.alpha3d:
        alpha_step = (args.amax - args.amin) / args.alen
        alphas += [round(args.amin + i*alpha_step, 4) for i in range(args.alen)]


    if args.maps:
        print_maps(N_INs, bases, mappings, args.outfile)
    elif args.load is not None:
        results = load_results(args.load)
    else:
        results = calculate_results(bases, N_INs, mappings, alphas)

    if args.dump:
        dump_results(results, args.outfile)

    if args.tables:
        print_tables(alphas, N_INs, bases, mappings, args.outfile, results)
    elif (args.interactive or args.png or args.svg) and not args.alpha3d:
        plot_graphs(alphas, N_INs, bases, mappings, results,
                     interactive=args.interactive, png=args.png, svg=args.svg)
    elif args.alpha3d and (args.interactive or args.png):
        plot_alpha3d(alphas, N_INs, bases, mappings, results,
                     interactive=args.interactive, png=args.png)
# }}} main
