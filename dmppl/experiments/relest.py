#!/usr/bin/env python3

# Relationship Estimation Metrics for Binary SoC Data
# https://arxiv.org/abs/1905.12465
#
# Generate some realistic looking data with known relationships, then apply
# various distance/similarity/correlation metrics and compare them.
# Dave McEwan 2019-04-09
#
# Run like:
#    relest.py score
#   OR
#    relest.py exportcsv
# Output directory is ./relest.<date>.results/
#
# Regenerate results for paper with:
#   time (./relest.py -v score && ./relest.py -v exportcsv --load-estimated)

# Single time window with single behaviour.
#   ==> Rectangular window is fine.
#   ==> Only a single delta (0) required.
#   - Fixed large n_times.
# Use very small values, or zero, for epsilon.
#   - Epsilons are only there for compression, not measuring.
# Save generated "measurement" data as EVS.
#   - Can convert to VCD later.
#   - system_n_(AND|OR|XOR|MIX).evs
# Save connection adjacency matrix.
#   - Rows are "from", columns are "to".
#   - Only one corner should be non-zero.
# Save similarity adjacency matrices.
#   - Difference is then just a matrix subtraction.
# Save true-positive, true-negative, false-positive, false-negative matrices.
# 5 types of experiment, evenly split between n_sys.
#   - AND - dst value is AND of connected sources.
#   - OR - dst value is OR of connected sources.
#   - XOR - dst value is XOR of connected sources.
#   - MIX - dst value is result of homogenously connected sources.
#       - Operations ~U(AND, OR, XOR)
#   - LHA - dst value is Left-Hand-Associative result of connected sources.
#       - Operations ~U(AND, OR, XOR)
# Over the number of systems n_srcs~U(1,50), n_dsts~U(1,50).
# Pr of each src ~Arcsine.
# Number of connection to each dst ~Lognormal(0,1).

# NOTE: Python3 uses generator zip() which saves significant memory vs Python2.

from __future__ import print_function

import argparse
import datetime
import glob
import numpy as np
from numpy.random import choice, uniform, lognormal
import os
from random import sample
import subprocess
import sys

# NOTE: dmppl doesn't include these packages by default so you need to install
# them manually with something like:
#   source venv3.7/bin/activate && pip install joblib prettytable seaborn
from joblib import Parallel, delayed
from prettytable import PrettyTable
import seaborn as sns
import matplotlib
matplotlib.use("Agg") # Don't require X11.
import matplotlib.pyplot as plt

from dmppl.base import *
from dmppl.math import *
from dmppl.nd import *
from dmppl.yaml import *
import dmppl.stats
from relest_learn import getMetric

__version__ = "0.1.0"

# Global for convenience since it's used all over the place.
outdir = None

metrics = [
    ("Ham", ndHam),
    ("Tmt", ndTmt),
    ("Cls", ndCls),
    ("Cos", ndCos),
    ("Cov", ndCov),
    ("Dep", ndDep),
]
nMetrics = None     # Initialized by main()
metricNames = None  # Initialized by main()

# https://en.wikipedia.org/wiki/Confusion_matrix
# https://en.wikipedia.org/wiki/Evaluation_of_binary_classifiers
stats = [
    ("TPR",  dmppl.stats.truePositiveRate),
    ("TNR",  dmppl.stats.trueNegativeRate),
    ("PPV",  dmppl.stats.positivePredictiveValue),
    ("NPV",  dmppl.stats.negativePredictiveValue),
    ("ACC",  dmppl.stats.accuracy),
    ("BACC", dmppl.stats.balancedAccuracy),
    ("MCC",  dmppl.stats.matthewsCorrelation),
    ("BMI",  dmppl.stats.bookmakersInformedness),
]
nStats = len(stats)
statNames = [nm for nm,fn in stats]


def arcsine_invCDF(u): # {{{
    '''Arcsine distribution inverse CDF
    '''
    u = float(u)
    assert 0 < u < 1

    r = 0.5 - 0.5 * np.cos(np.pi * u)
    return float(r)
# }}} def arcsine_invCDF

def constructSystem(sysNum, n_maxm): # {{{

    systems_dir = joinP(outdir, "systems")
    mkDirP(systems_dir)

    # Type of system.
    # 0 - only AND
    # 1 - only OR
    # 2 - only XOR
    # 3 - monogamous mix
    # 4 - LHA mix
    sysType = int(choice(range(5)))

    # Unique name allowing simple id/search.
    name = "system%06d" % (sysNum)

    # Number of measurement nodes.
    n_src = int(np.ceil(uniform() * (n_maxm-1))) + 1
    n_dst = int(np.ceil(uniform() * (n_maxm-1))) + 1
    m = n_src + n_dst
    assert isinstance(n_src, int)
    assert isinstance(n_dst, int)
    assert 1 < n_src <= n_maxm, n_src
    assert 1 < n_dst <= n_maxm, n_dst

    # Densities for src nodes.
    density = [arcsine_invCDF(i) for i in uniform(size=n_src)]
    assert len(density) == n_src

    # Number of connections for dst nodes.
    n_con = [int(np.minimum(np.rint(i)+1, n_src)) \
             for i in lognormal(0, 1, n_dst)]
    assert len(n_con) == n_dst
    for n in n_con:
        assert 0 < n <= n_src

    # List of lists of src indexes for the connections to each dst.
    consrc = [sample(range(n_src), k) for k in n_con]
    assert len(consrc) == n_dst, "Need a list of sources for each dst."

    # Operations used to combine connections.
    assert sysType in range(5)
    if sysType in [0,1,2]: # all AND/OR/XOR
        conop = [[None] + [sysType]*(n-1) \
                 for n in n_con]
    elif sysType == 3: # monogamous mix
        conop = [[None] + [int(choice(range(3)))]*(n-1) \
                 for n in n_con]
    elif sysType == 4: # LHA mix
        conop = [[None] + [int(choice(range(3))) for ss in range(n-1)] \
                 for n in n_con]
    assert len(conop) == n_dst, "Need a list of operations for each dst."

    for i,(s,o) in enumerate(zip(consrc, conop)):
        assert len(s) <= n_src, "Too many connection sources."
        assert len(set(s)) == len(s), "Non-unique connection sources."
        assert len(s) == len(o), "Unmatched operation sources."

        for ss in s:
            assert 0 <= ss < n_src, "Out-of-range connection source."

        for j,oo in enumerate(o):
            if 0 == j:
                assert oo is None
            else:
                assert oo in range(3), "Out-of-range operation source."

    # Save system in YAML format.
    system = {
        "sysType": sysType,
        "name": name,
        "n_src": n_src,
        "n_dst": n_dst,
        "m": m,
        "density": density,
        "n_con": n_con,
        "consrc": consrc,
        "conop": conop,
    }
    saveYml(system, joinP(systems_dir, system["name"]))

    return system
# }}} def constructSystem

def systemKnown(system): # {{{

    m = system["m"]
    consrc = system["consrc"]
    n_src = system["n_src"]
    n_dst = system["n_dst"]

    knowns_dir = joinP(outdir, "knowns")
    mkDirP(knowns_dir)

    # Save matrix of known relationships.
    # Rows -> "from", columns -> "to".
    known = np.zeros((m, m), dtype=np.bool) # Asymmetric, upper-triangular.
    for d in range(n_dst):
        for ss in consrc[d]:
            known[ss][n_src + d] = True

    fname_known = joinP(knowns_dir, system["name"] + ".known")
    saveNpy(known, fname_known)
    np.savetxt(fname_known + ".txt", known.astype(np.int),
               fmt='%d', delimiter='')

    return known
# }}} def systemKnown

def generateSamples(system, n_time): # {{{
    sysname = system["name"]
    n_src = system["n_src"]
    density = system["density"]
    consrc = system["consrc"]
    conop = system["conop"]

    assert len(consrc) == len(conop)
    n_dst = len(consrc)
    assert n_dst == system["n_dst"]

    EVSs_dir = joinP(outdir, "evs")
    mkDirP(EVSs_dir)

    # EVS for src nodes.
    evs_src = np.stack([uniform(size=n_time) < density[i] \
                        for i in range(n_src)]).astype(np.bool)

    #fname_evs_src = joinP(EVSs_dir, sysname + ".evs.src")
    #saveNpy(evs_src, fname_evs_src)
    #np.savetxt(fname_evs_src + ".txt", evs_src.astype(np.int),
    #           fmt='%d', delimiter='')

    # Calculate values of dst nodes.
    evs_dst = np.empty((n_dst, n_time), dtype=np.bool)
    for t in range(n_time):
        for d in range(n_dst):
            v = False

            for ss,oo in zip(consrc[d], conop[d]):
                src_v = evs_src[ss][t]

                if oo is None:
                    v = src_v
                else:
                    assert oo in [0,1,2]
                    op = [np.logical_and,
                          np.logical_or,
                          np.logical_xor][oo]
                    v = op(v, src_v)

            evs_dst[d][t] = v

    evs = np.vstack((evs_src, evs_dst))
    fname_evs_full = joinP(EVSs_dir, sysname + ".evs")
    np.savetxt(fname_evs_full + ".txt", evs.astype(np.int),
               fmt='%d', delimiter='')
    saveNpy(evs, fname_evs_full)
    return
# }}} def generateSamples

def exportCsv(system, evs, known, estimated, n_time): # {{{
    '''Write a CSV file for a single system containing various metrics on the
    node-to-node relationships.

    This is intended to be used as a dataset to feed a learning model.
    '''

    csvDir = joinP(outdir, "csv")
    mkDirP(csvDir)

    sysname = system["name"]
    fnameCsv = joinP(csvDir, sysname + ".csv")

    # [ (<title>, <format>), ... ]
    columns = [
        ("xNode",       "{Xnode:d}"),
        ("yNode",       "{Ynode:d}"),
        ("known",       "{known_XpairY:d}"),
        ("E[X]",       "{Ex_X:0.6f}"),
        ("E[Y]",       "{Ex_Y:0.6f}"),
        ("E[X|Y]",     "{Ex_XgivenY:0.6f}"),
        ("E[Y|X]",     "{Ex_YgivenX:0.6f}"),
        ("E[X*Y]",     "{Ex_XconvY:0.6f}"),
        ("E[|X-Y|]",   "{Ex_XabsdifY:0.6f}"),
        ('"Ham(X,Y)"',  "{Ham:0.6f}"),
        ('"Tmt(X,Y)"',  "{Tmt:0.6f}"),
        ('"Cls(X,Y)"',  "{Cls:0.6f}"),
        ('"Cos(X,Y)"',  "{Cos:0.6f}"),
        ('"Cov(X,Y)"',  "{Cov:0.6f}"),
        ('"Dep(X,Y)"',  "{Dep:0.6f}"),
    ]
    titleLine = ",".join([t for t,f in columns])
    lineFmt = ",".join([f for t,f in columns])

    m = system["m"]
    assert m == len(evs), (m, len(evs))
    assert known.shape == (m,m), (known.shape, m)

    #W = powsineCoeffs(n_time, 0) # Rectangular
    #W = powsineCoeffs(n_time, 1) # Sine
    W = powsineCoeffs(n_time, 2) # Raised Cosine
    #W = powsineCoeffs(n_time, 4) # Alternative Blackman

    with open(fnameCsv, 'w') as fd:
        print(titleLine, file=fd)

        # NOTE: All metrics are symmetrical,
        for i in range(m): # Row
            for j in range(i+1, m): # Column. Upper triangle only.

                X = evs[i]
                Y = evs[j]

                # Find known value.
                known_XpairY = known[i][j]

                # Calculate E[]s
                Ex_X = ndEx(W, X)
                Ex_Y = ndEx(W, Y)
                Ex_XgivenY = np.nan_to_num(ndCex(W, X, Y))
                Ex_YgivenX = np.nan_to_num(ndCex(W, Y, X))

                Ex_XconvY = ndEx(W, ndConv(X, Y))

                Ex_XabsdifY = ndEx(W, ndAbsDiff(X, Y))

                # Lookup metrics from previous calculation.
                Ham = estimated[metricNames.index("Ham")][i][j]
                Tmt = estimated[metricNames.index("Tmt")][i][j]
                Cls = estimated[metricNames.index("Cls")][i][j]
                Cos = estimated[metricNames.index("Cos")][i][j]
                Cov = estimated[metricNames.index("Cov")][i][j]
                Dep = estimated[metricNames.index("Dep")][i][j]

                line = lineFmt.format(
                    Xnode       =i,
                    Ynode       =j,
                    known_XpairY=known_XpairY,
                    Ex_X        =Ex_X,
                    Ex_Y        =Ex_Y,
                    Ex_XgivenY  =Ex_XgivenY,
                    Ex_YgivenX  =Ex_YgivenX,
                    Ex_XconvY   =Ex_XconvY,
                    Ex_XabsdifY =Ex_XabsdifY,
                    Ham         =Ham,
                    Tmt         =Tmt,
                    Cls         =Cls,
                    Cos         =Cos,
                    Cov         =Cov,
                    Dep         =Dep,
                )
                print(line, file=fd)

    return
# }}} def exportCsv

def combineCsvs(): # {{{
    '''Combine all CSV files into one.

    Equivalent to:
      head -n+1 system000000.csv > combined.csv
      awk 'FNR>1' system*.csv >> combined.csv
    '''
    fnameis = glob.glob(joinP(outdir, "csv", "system*.csv"))
    fnameo = joinP(outdir, "csv", "combined.csv")

    # Copy header from first CSV.
    with open(fnameo, 'w') as fd:
        ret = subprocess.call(("head", "-n+1", fnameis[0]), stdout=fd)
        if 0 != ret:
            return ret

    # Append bodies from all CSVs.
    with open(fnameo, 'a') as fd:
        ret = subprocess.call(["awk", "FNR>1"] + fnameis, stdout=fd)
        return ret
# }}} def combineCsvs

def performEstimations(system, evs, n_time): # {{{

    estimateds_dir = joinP(outdir, "estimated")
    mkDirP(estimateds_dir)

    m = system["m"]

    #W = powsineCoeffs(n_time, 0) # Rectangular
    #W = powsineCoeffs(n_time, 1) # Sine
    W = powsineCoeffs(n_time, 2) # Raised Cosine
    #W = powsineCoeffs(n_time, 4) # Alternative Blackman

    # Calculate similarity metrics.
    fname_estimated = joinP(estimateds_dir, system["name"] + ".estimated")
    estimated = np.zeros((nMetrics, m, m))
    for i in range(m): # Row "from"
        for j in range(i+1, m): # Column "to". Upper triangle only.

            for f,(nm,fn) in enumerate(metrics):
                estimated[f][i][j] = fn(W, evs[j], evs[i])
                np.savetxt(fname_estimated + ".%s.txt" % nm,
                           estimated[f], fmt='%0.03f')

    saveNpy(estimated, fname_estimated)
    return
# }}} def performEstimations

def scoreSystem(system, known, estimated): # {{{

    # Calculate confusion matrix for each metric in parallel.
    kno_pos = np.asarray([known for _ in estimated])
    kno_neg = 1 - kno_pos
    est_pos = estimated
    est_neg = 1 - estimated
    TN = np.sum(np.triu(np.minimum(kno_neg, est_neg), 1), axis=(1,2))
    TP = np.sum(np.triu(np.minimum(kno_pos, est_pos), 1), axis=(1,2))
    FN = np.sum(np.triu(np.minimum(kno_pos, est_neg), 1), axis=(1,2))
    FP = np.sum(np.triu(np.minimum(kno_neg, est_pos), 1), axis=(1,2))
    assert FN.shape == TN.shape == TP.shape == FP.shape == \
        (nMetrics,), (FN.shape, TN.shape, TP.shape, FP.shape)

    with np.errstate(divide='ignore', invalid='ignore'):
        sysScore = [fn(TP, FP, FN, TN) for nm,fn in stats]

    # Print score for this system in table.
    scoretable_dir = joinP(outdir, "scoretables")
    mkDirP(scoretable_dir)
    fname_table = joinP(scoretable_dir, system["name"] + ".table.txt")
    table = PrettyTable(["Metric"] + statNames)
    rows = zip(metricNames, *sysScore)
    for row in rows:
        rowStrings = [(col if 0 == i else "%.04f" % col) \
                      for i,col in enumerate(row)]
        table.add_row(rowStrings)
    #dbg(table)
    with open(fname_table, 'w') as fd:
        fd.write(str(table))

    return (system["sysType"], sysScore)
# }}} def scoreSystem

def tabulateScores(scoresByTypename): # {{{

    for sysTypename,scores in scoresByTypename:
        # NOTE scores.shape: (<n_sys>, <n_stats>, <n_metrics>)
        if 3 != len(scores.shape): continue # No systems of this type.

        # Average scores over all systems and tabulate.
        sysScoresMean = np.nanmean(scores, axis=0)

        table = PrettyTable(["Metric"] + statNames)
        rows = zip(metricNames, *sysScoresMean)
        for row in rows:
            rowStrings = [(col if 0 == i else "%.04f" % col) \
                          for i,col in enumerate(row)]
            table.add_row(rowStrings)

        #dbg(table)
        with open(joinP(outdir, "mean.%s.table.txt" % sysTypename), 'w') as fd:
            fd.write(str(table))

    return
# }}} def tabulateScores

def plotScores(scoresByTypename): # {{{

    plotDir = joinP(outdir, "plot")
    mkDirP(plotDir)
    plotPathFmtPdf = joinP(plotDir, "relest_%s_%s.pdf")
    plotPathFmtPng = joinP(plotDir, "relest_%s_%s.png")

    markers = [".", "o", "x", "^", "s", "*", "", "", "", ""]

    # figsize used to set dimensions in inches.
    # ax.set_aspect() doesn't work for KDE where Y-axis is scaled.
    figsize = (8, 5)

    fignum = 0
    for sysTypename,scores in scoresByTypename:
        # NOTE scores.shape: (<n_sys>, <n_stats>, <n_metrics>)
        if 3 != len(scores.shape): continue # No systems of this type.

        for s,statName in enumerate(statNames):

            fignum += 1; fig = plt.figure(fignum, figsize=figsize)

            for i,metricName in enumerate(metricNames):

                dataset = np.nan_to_num(scores[:, s, i])
                if 1 == dataset.shape[0]: # Seaborn won't plot single values.
                    # Repeat existing value to avoid crash.
                    dataset = [dataset[0], dataset[0]+1e-5]

                sns.kdeplot(dataset, label=metricName, marker=markers[i], markevery=5)

            plt.legend()
            plt.yticks([])
            plt.xlim(0, 1)
            plt.savefig(plotPathFmtPdf % (sysTypename, statName), bbox_inches="tight")
            plt.savefig(plotPathFmtPng % (sysTypename, statName), bbox_inches="tight")
            plt.close()

    return
# }}} def plot_scores

# {{{ argparser

argparser = argparse.ArgumentParser(
    description = "relest - Relationship Estimation Metrics for Binary SoC Data.",
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

nowStr = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
argparser.add_argument("outdir",
    nargs='?',
    type=str,
    default="relest.%s.results" % nowStr,
    help="Results directory.")

argparser.add_argument("action",
    type=str,
    default="score",
    choices=["score", "exportcsv"],
    help="What to do...")

argparser.add_argument("-q", "--quickdbg",
    default=False,
    action='store_true',
    help="Use very low preset values for n_time, n_sys, n_maxm. Just for debug.")

argparser.add_argument("-j", "--n_jobs",
    type=int,
    default=-2,
    help="Number of parallel jobs, where applicable.")

argparser.add_argument("-L", "--learned-metric-fnames",
    default=[],
    action='append',
    help="Filename of learned metric (JSON).")

argparser.add_argument("--load-system",
    default=False,
    action='store_true',
    help="Repeat with saved systems.")

argparser.add_argument("--load-evs",
    default=False,
    action='store_true',
    help="Repeat with saved systems and saved data.")

argparser.add_argument("--load-estimated",
    default=False,
    action='store_true',
    help="Repeat with saved systems, saved data, and saved estimations.")

argparser.add_argument("--load-score",
    default=False,
    action='store_true',
    help="Load and plot <outdir>/scores.*.npy.gz")

argparser.add_argument("--n_time",
    type=int,
    default=int(1e5),
    help="Number of times.")

argparser.add_argument("--n_sys",
    type=int,
    default=int(1e3),
    help="Number of systems.")

argparser.add_argument("--n_maxm",
    type=int,
    default=50,
    help="Maximum number of src/dst nodes.")

# }}} argparser

def main(args): # {{{
    '''
    System topology generated with a mixture of Python and NumPy PRNGs.
    Measurement data generated with NumPy PRNG.
    '''

    global outdir
    outdir = args.outdir

    mkDirP(outdir)
    verb("outdir: %s" % outdir)

    if args.quickdbg:
        args.n_time = 20
        args.n_sys = 20
        args.n_maxm = 10

    global metrics
    global metricNames
    global nMetrics
    metrics += [getMetric(fnameAppendExt(fname, "metric.json")) \
                for fname in args.learned_metric_fnames]
    nMetrics = len(metrics)
    metricNames = [nm for nm,fn in metrics]

    # Use of generator comprehensions allows only required data to be
    # either generated or read from file once.
    if args.load_score:      args.load_estimated = True
    if args.load_estimated:  args.load_evs = True
    if args.load_evs:        args.load_system = True

    load_system = args.load_system
    make_system = not load_system
    load_evs = args.load_evs
    load_estimated = args.load_estimated

    if args.action == "exportcsv":
        load_score = False
        make_score = False
    elif args.action == "score":
        load_score = args.load_score
        make_score = not load_score


    # Construct systems with known relationships.
    if load_system:
        verb("Loading systems... ", end='')

        systems_fname_fmt = joinP(outdir, "systems", "system*.yml")
        systems_fnames = sorted([f for f in glob.glob(systems_fname_fmt)])
        systems = [loadYml(f) for f in systems_fnames]
        assert len(systems) == len(systems_fnames)

        knowns_fname_fmt = joinP(outdir, "knowns", "system*.known.npy.gz")
        knowns_fnames = sorted([f for f in glob.glob(knowns_fname_fmt)])
        assert len(systems) == len(knowns_fnames)
        knowns = (loadNpy(f) for f in knowns_fnames)

        n_sys = len(systems)
        verb("Done")
    elif make_system:
        verb("Constructing systems... ", end='')
        n_sys = args.n_sys
        systems = [constructSystem(sysNum, args.n_maxm) \
                   for sysNum in range(n_sys)]
        knowns = (systemKnown(system) for system in systems)
        verb("Done")


    # Generate and write EVent Samples (EVS) from constructed systems to disk.
    if not load_evs:
        verb("Generating EVSs... ", end='', sv_tm=True)
        n_time = args.n_time
        _ = Parallel(n_jobs=args.n_jobs) \
                (delayed(generateSamples)(system, n_time) \
                    for system in systems)
        verb("Done", rpt_tm=True)

    # Lazily read EVS from disk.
    verb("Loading EVSs... ", end='')
    EVSs_fname_fmt = joinP(outdir, "evs", "system*.evs.npy.gz")
    EVSs_fnames = sorted([f for f in glob.glob(EVSs_fname_fmt)])
    assert len(systems) == len(EVSs_fnames)
    EVSs = (loadNpy(f) for f in EVSs_fnames)

    n_time = loadNpy(EVSs_fnames[0]).shape[1]
    verb("Lazy")


    # Perform estimations on generated data and write out to disk.
    if not load_estimated:
        verb("Performing estimations... ", end='', sv_tm=True)
        _ = Parallel(n_jobs=args.n_jobs) \
                (delayed(performEstimations)(system, evs, n_time) \
                    for system,evs in zip(systems, EVSs))
        verb("Done", rpt_tm=True)

        # Redefine generator to allow it to be reconsumed later by exportcsv.
        EVSs = (loadNpy(f) for f in EVSs_fnames)

    # Lazily read estimations from disk.
    verb("Loading estimations... ", end='')
    estimateds_fname_fmt = joinP(outdir, "estimated", "system*.estimated.npy.gz")
    estimateds_fnames = sorted([f for f in glob.glob(estimateds_fname_fmt)])
    assert len(systems) == len(estimateds_fnames)
    estimateds = (loadNpy(f) for f in estimateds_fnames)
    verb("Lazy")


    if args.action == "exportcsv":
        # NOTE: Incomplete and probably broken.
        verb("Exporting CSVs... ", end='', sv_tm=True)
        for system,evs,known,estimated in zip(systems,EVSs,knowns,estimateds):
            exportCsv(system, evs, known, estimated, n_time)
        verb("Done", rpt_tm=True)

        verb("Combining CSVs... ", end='', sv_tm=True)
        combineCsvs()
        verb("Done", rpt_tm=True)

    elif args.action == "score":

        fnameFmtScores = joinP(outdir, "scores.%s")
        sysTypenames = ["and", "or", "xor", "mix", "lha"] # "all" is appended

        if load_score:
            verb("Loading scores... ", end='')
            scoresByTypename = [(sysTypename, loadNpy(fnameFmtScores % sysTypename)) \
                                for sysTypename in sysTypenames + ["all"]]
            verb("Done")
        elif make_score:
            verb("Scoring metric performance of each system... ", end='', sv_tm=True)
            # Parallelize (one job per system) scoring which includes performing
            # or loading the estimations since they are lazy.
            # NOTE: scores is ( (<sysType>, <sysScore>), ... )
            scores = Parallel(n_jobs=args.n_jobs) \
                (delayed(scoreSystem)(s, k, e) \
                    for s,k,e in zip(systems,knowns,estimateds))
            verb("Done", rpt_tm=True)

            # NOTE: Each score ndarray shape is (<n_sys>, <nStats>, <nMetrics>)
            scoresByTypename = \
                [(sysTypename, np.asarray([score for t,score in scores if t == i]) ) \
                 for i,sysTypename in enumerate(sysTypenames)] + \
                [("all", np.asarray([score for _,score in scores]))]

            verb("Saving scores... ", end='')
            for sysTypename,monotypeScores in scoresByTypename:
                saveNpy(monotypeScores, fnameFmtScores % sysTypename)
            verb("Done")

        verb("Tabulating... ", end='', sv_tm=True)
        tabulateScores(scoresByTypename)
        verb("Done", rpt_tm=True)

        verb("Plotting... ", end='', sv_tm=True)
        plotScores(scoresByTypename)
        verb("Done", rpt_tm=True)

    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())
