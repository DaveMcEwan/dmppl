#!/usr/bin/env python3

# Relationship Estimation Metrics for Binary SoC Data
# https://arxiv.org/abs/1905.12465
#
# Generate some realistic looking data with known relationships, then apply
# various distance/similarity/correlation metrics and compare them.
# Dave McEwan 2019-04-09
#
# Run like:
#    relest.py scoreplot
#   OR
#    relest.py exportcsv
# Output directory is ./results/
#
# Regenerate results for paper with:
#   time (./relest.py -v scoreplot && ./relest.py -v exportcsv --load-estimated)

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
import numpy as np
from numpy.random import choice, uniform, lognormal
from random import sample
import os
import sys
import glob

# NOTE: dmppl doesn't include these packages by default so you need to install
# them manually with something like:
#   source venv3.7/bin/activate && pip install prettytable seaborn
from prettytable import PrettyTable
import seaborn as sns
import matplotlib
matplotlib.use("Agg") # Don't require X11.
import matplotlib.pyplot as plt

from dmppl.base import *
from dmppl.math import *
from dmppl.nd import *
from dmppl.yaml import *

__version__ = "0.1.0"

# Global for convenience since it's used all over the place.
outdir = None

statNames = ["TPR", "TNR", "PPV", "NPV", "ACC", "BACC", "MCC", "BMI"]

def arcsine_invCDF(u): # {{{
    '''Arcsine distribution inverse CDF
    '''
    u = float(u)
    assert 0 < u < 1

    r = 0.5 - 0.5 * np.cos(np.pi * u)
    return float(r)
# }}} def arcsine_invCDF

def construct_system(sysnum, n_maxm): # {{{

    systems_dir = outdir + "systems" + os.sep
    mkDirP(systems_dir)

    # Type of system.
    # 0 - all AND
    # 1 - all OR
    # 2 - all XOR
    # 3 - monogamous mix
    # 4 - LHA mix
    systype = int(choice(range(5)))

    # Unique name allowing simple id/search.
    name = "system%06d" % (sysnum)

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
    assert systype in range(5)
    if systype in [0,1,2]: # all AND/OR/XOR
        conop = [[None] + [systype]*(n-1) \
                 for n in n_con]
    elif systype == 3: # monogamous mix
        conop = [[None] + [int(choice(range(3)))]*(n-1) \
                 for n in n_con]
    elif systype == 4: # LHA mix
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
        "systype": systype,
        "name": name,
        "n_src": n_src,
        "n_dst": n_dst,
        "m": m,
        "density": density,
        "n_con": n_con,
        "consrc": consrc,
        "conop": conop,
    }
    saveYml(system, systems_dir + system["name"])

    return system
# }}} def construct_system

def system_known(system): # {{{

    m = system["m"]
    consrc = system["consrc"]
    n_src = system["n_src"]
    n_dst = system["n_dst"]

    knowns_dir = outdir + "knowns" + os.sep
    mkDirP(knowns_dir)


    # Save matrix of known relationships.
    # Rows -> "from", columns -> "to".
    known = np.zeros((m, m), dtype=np.bool) # Asymmetric, upper-triangular.
    for d in range(n_dst):
        for ss in consrc[d]:
            known[ss][n_src + d] = True

    fname_known = knowns_dir + system["name"] + ".known"
    saveNpy(known, fname_known)
    np.savetxt(fname_known + ".txt", known.astype(np.int),
               fmt='%d', delimiter='')

    return known
# }}} def system_known

def generate_evs(system, n_time): # {{{
    sysname = system["name"]
    n_src = system["n_src"]
    density = system["density"]
    consrc = system["consrc"]
    conop = system["conop"]

    assert len(consrc) == len(conop)
    n_dst = len(consrc)
    assert n_dst == system["n_dst"]

    EVSs_dir = outdir + "evs" + os.sep
    mkDirP(EVSs_dir)

    # EVS for src nodes.
    evs_src = np.stack([uniform(size=n_time) < density[i] \
                        for i in range(n_src)]).astype(np.bool)

    #fname_evs_src = EVSs_dir + sysname + ".evs.src"
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
    fname_evs_full = EVSs_dir + sysname + ".evs"
    saveNpy(evs, fname_evs_full)
    np.savetxt(fname_evs_full + ".txt", evs.astype(np.int),
               fmt='%d', delimiter='')
    return evs
# }}} def generate_evs

def export_csv_KnownMeasured(system, evs, known, estimated, n_time, metrics): # {{{

    def metricIndex(nm):
        nms = [m[0] for m in metrics]
        return indexDefault(nms, nm)

    Ham_idx = metricIndex("Ham")
    Tmt_idx = metricIndex("Tmt")
    Cls_idx = metricIndex("Cls")
    Cos_idx = metricIndex("Cos")
    Cov_idx = metricIndex("Cov")
    Dep_idx = metricIndex("Dep")

    csv_dir = outdir + "csv" + os.sep
    mkDirP(csv_dir)

    line_fmt = ", ".join([
        "{known_XpairY:d}",
        "{Ex_X:0.6f}",
        "{Ex_Y:0.6f}",
        "{Ex_XgivenY:0.6f}",
        "{Ex_YgivenX:0.6f}",
        "{Ex_XconvY:0.6f}",
        "{Ex_XabsdifY:0.6f}",
        "{Ham:0.6f}", # Reflection of Ex_XabsdifY.
        "{Tmt:0.6f}",
        "{Cls:0.6f}",
        "{Cos:0.6f}",
        "{Cov:0.6f}",
        "{Dep:0.6f}",
    ])

    sysname = system["name"]
    m = system["m"]
    assert m == len(evs), (m, len(evs))
    assert known.shape == (m,m), (known.shape, m)

    #W = powsineCoeffs(n_time, 0) # Rectangular
    #W = powsineCoeffs(n_time, 1) # Sine
    W = powsineCoeffs(n_time, 2) # Raised Cosine
    #W = powsineCoeffs(n_time, 4) # Alternative Blackman

    fname_csv = csv_dir + sysname + ".KnownMeasured.csv"
    with open(fname_csv, 'a') as fd:
        for i in range(m): # Row "from"
            for j in range(i+1, m): # Column "to". Upper triangle only.

                X = evs[j]
                Y = evs[i]

                # Find known value.
                known_XpairY = known[i][j]

                # Calculate E[]s
                Ex_X = ndEx(W, X)
                Ex_Y = ndEx(W, Y)
                Ex_XgivenY = np.nan_to_num(ndCex(W, X, Y))
                Ex_YgivenX = np.nan_to_num(ndCex(W, Y, X))

                Ex_XconvY = ndEx(W, ndConv(X, Y))

                Ex_XabsdifY = ndEx(W, ndAbsDiff(X, Y))

                # Calculate metrics.
                Ham = ndHam(W, X, Y) if Ham_idx is None else estimated[Ham_idx][i][j]
                Tmt = ndTmt(W, X, Y) if Tmt_idx is None else estimated[Tmt_idx][i][j]
                Cls = ndCls(W, X, Y) if Cls_idx is None else estimated[Cls_idx][i][j]
                Cos = ndCos(W, X, Y) if Cos_idx is None else estimated[Cos_idx][i][j]
                Cov = ndCov(W, X, Y) if Cov_idx is None else estimated[Cov_idx][i][j]
                Dep = ndDep(W, X, Y) if Dep_idx is None else estimated[Dep_idx][i][j]

                # Format into data line.
                line = line_fmt.format(
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
                fd.write(line + '\n')

    return 0
# }}} def export_csv_KnownMeasured

def estimate_similarities(system, metrics, evs, n_time): # {{{

    estimateds_dir = outdir + "estimated" + os.sep
    mkDirP(estimateds_dir)

    nMetrics = len(metrics)
    m = system["m"]

    #W = powsineCoeffs(n_time, 0) # Rectangular
    #W = powsineCoeffs(n_time, 1) # Sine
    W = powsineCoeffs(n_time, 2) # Raised Cosine
    #W = powsineCoeffs(n_time, 4) # Alternative Blackman

    # Calculate similarity metrics.
    fname_estimated = estimateds_dir + system["name"] + ".estimated"
    estimated = np.zeros((nMetrics, m, m))
    for i in range(m): # Row "from"
        for j in range(i+1, m): # Column "to". Upper triangle only.

            for f,(nm,fn) in enumerate(metrics):
                estimated[f][i][j] = fn(W, evs[j], evs[i])
                np.savetxt(fname_estimated + ".%s.txt" % nm,
                           estimated[f], fmt='%0.03f')
    saveNpy(estimated, fname_estimated)
    return estimated
# }}} def estimate_similarities

def compare_scores(system, known, estimated, metrics, scorespace): # {{{
    nMetrics = len(metrics)
    metricNames = [nm for nm,fn in metrics]

    scores_and = scorespace[0]
    scores_or  = scorespace[1]
    scores_xor = scorespace[2]
    scores_mix = scorespace[3]
    scores_lha = scorespace[4]
    scores_all = scorespace[5]

    # Calculate similarity metrics into matrices and compare.
    kno_pos = np.asarray([known for _ in estimated])
    kno_neg = 1 - kno_pos
    mea_pos = estimated
    mea_neg = 1 - estimated
    TN = np.sum(np.triu(np.minimum(kno_neg, mea_neg), 1), axis=(1,2))
    TP = np.sum(np.triu(np.minimum(kno_pos, mea_pos), 1), axis=(1,2))
    FN = np.sum(np.triu(np.minimum(kno_pos, mea_neg), 1), axis=(1,2))
    FP = np.sum(np.triu(np.minimum(kno_neg, mea_pos), 1), axis=(1,2))
    assert FN.shape == TN.shape == TP.shape == FP.shape == \
        (nMetrics,), (FN.shape, TN.shape, TP.shape, FP.shape)

    # Higher is always better.
    # https://en.wikipedia.org/wiki/Confusion_matrix
    # https://en.wikipedia.org/wiki/Evaluation_of_binary_classifiers
    with np.errstate(divide='ignore', invalid='ignore'):

        # True Positive Rate, Sensitivity, Recall
        TPR = TP / (TP + FN)

        # True Negative Rate, Specificity, Selectivity
        TNR = TN / (TN + FP)

        # Positive Predictive Value, Precision
        PPV = TP / (TP + FP)

        # Negative Predictive Value
        NPV = TN / (TN + FN)

        # Accuracy
        # NOTE: does not perform well with imbalanced data sets.
        ACC = (TN + TP) / (TN + TP + FN + FP)

        # Balanced Accuracy
        BACC = (TPR + TNR) / 2

        # Matthews Correlation Coefficient
        # https://en.wikipedia.org/wiki/Matthews_correlation_coefficient
        MCC = (TP*TN - FP*FN) / np.sqrt((TP+FP) * (TP+FN) * (TN+FP) * (TN+FN))

        # Book-Maker's Informedness, Youden's_J_statistic
        # https://en.wikipedia.org/wiki/Youden%27s_J_statistic
        BMI = TPR + TNR - 1

    assert (nMetrics,) == TPR.shape == TNR.shape \
                       == PPV.shape == NPV.shape \
                       == ACC.shape == BACC.shape \
                       == MCC.shape == BMI.shape, \
        (nMetrics, TPR.shape, TNR.shape,
                   PPV.shape, NPV.shape,
                   ACC.shape, BACC.shape,
                   MCC.shape, BMI.shape)

    system_score = [TPR, TNR, PPV, NPV, ACC, BACC, MCC, BMI]

    # Print score for this system in table.
    scoretable_dir = outdir + "scoretables" + os.sep
    mkDirP(scoretable_dir)
    fname_table = scoretable_dir + system["name"] + ".table.txt"
    table = PrettyTable(["Metric"] + statNames)
    rows = zip(metricNames, *system_score)
    for row in rows:
        rowStrings = [(col if 0 == i else "%.04f" % col) \
                      for i,col in enumerate(row)]
        table.add_row(rowStrings)
    #dbg(table)
    with open(fname_table, 'w') as fd:
        fd.write(str(table))

    scores_all.append(system_score)

    systype = system["systype"]
    if 0 == systype: scores_and.append(system_score)
    elif 1 == systype: scores_or.append(system_score)
    elif 2 == systype: scores_xor.append(system_score)
    elif 3 == systype: scores_mix.append(system_score)
    elif 4 == systype: scores_lha.append(system_score)

    return None
# }}} def compare_scores

def plot_scores(metrics, scores_conglomerate): # {{{

    metricNames = [nm for nm,fn in metrics]

    plot_dir = outdir + "plot" + os.sep
    mkDirP(plot_dir)

    markers = [".", "o", "x", "^", "s", "*", "", "", "", ""]

    # figsize used to set dimensions in inches.
    # ax.set_aspect() doesn't work for KDE where Y-axis is scaled.
    figsize = (8, 5)

    fignum = 0
    for res_nm,scores in scores_conglomerate:
        # NOTE scores.shape: (<n_sys>, <n_stats>, <n_metrics>)
        if 3 != len(scores.shape): continue # No systems of this type.

        # Average scores over all systems and tabulate.
        system_mean = np.mean(scores, axis=0)

        fname_avgd = outdir + "mean.%s.table.txt" % res_nm
        table_avgd = PrettyTable(["Metric"] + statNames)
        rows = zip(metricNames, *system_mean)
        for row in rows:
            rowStrings = [(col if 0 == i else "%.04f" % col) \
                          for i,col in enumerate(row)]
            table_avgd.add_row(rowStrings)

        #dbg(table_avgd)
        with open(fname_avgd, 'w') as fd:
            fd.write(str(table_avgd))

        for c,cmp_nm in enumerate(statNames):

            fignum += 1; fig = plt.figure(fignum, figsize=figsize)

            for i,nm in enumerate(metricNames):

                dataset = np.nan_to_num(scores[:, c, i])
                if 1 == dataset.shape[0]: # Seaborn won't plot single values.
                    # Repeat existing value to avoid crash.
                    dataset = [dataset[0], dataset[0]+1e-5]

                sns.kdeplot(dataset, label=nm, marker=markers[i], markevery=5)

            plt.legend()
            plt.yticks([])
            plt.xlim(0, 1)
            plt.savefig(plot_dir + "relest_%s_%s.pdf" % (res_nm, cmp_nm),
                        bbox_inches="tight")
            plt.savefig(plot_dir + "relest_%s_%s.png" % (res_nm, cmp_nm),
                        bbox_inches="tight")
            plt.close()

    return 0
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
    default="scoreplot",
    choices=["scoreplot", "exportcsv"],
    help="What to do...")

argparser.add_argument("-q", "--quickdbg",
    default=False,
    action='store_true',
    help="Use very low preset values for n_time, n_sys, n_maxm. Just for debug.")

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
    outdir = args.outdir + \
        ("" if args.outdir.endswith(os.sep) else os.sep)

    if args.quickdbg:
        args.n_time = 20
        args.n_sys = 20
        args.n_maxm = 10

    mkDirP(outdir)

    metrics = [
        #("cEx", ndCex),
        ("Ham", ndHam),
        ("Tmt", ndTmt),
        ("Cls", ndCls),
        ("Cos", ndCos),
        ("Cov", ndCov),
        ("Dep", ndDep),
    ]
    nMetrics = len(metrics)

    # Use of generator comprehensions allows only required data to be
    # either generated or read from file once.
    if args.load_estimated:  args.load_evs = True
    if args.load_evs:       args.load_system = True

    load_system = args.load_system
    make_system = not load_system
    load_evs = args.load_evs
    make_evs = not load_evs
    load_estimated = args.load_estimated
    make_estimated = not load_estimated

    if args.action == "exportcsv":
        load_score = False
        make_score = False
    elif args.action == "scoreplot":
        load_score = args.load_score
        make_score = not load_score


    # Construct systems with known relationships.
    if load_system:
        verb("Loading systems... ", end='')

        systems_fname_fmt = outdir + "systems" + os.sep + \
                            "system*.yml"
        systems_fnames = sorted([f for f in glob.glob(systems_fname_fmt)])
        systems = [loadYml(f) for f in systems_fnames]
        assert len(systems) == len(systems_fnames)

        knowns_fname_fmt = outdir + "knowns" + os.sep + \
                           "system*.known.npy.gz"
        knowns_fnames = sorted([f for f in glob.glob(knowns_fname_fmt)])
        assert len(systems) == len(knowns_fnames)
        knowns = (loadNpy(f) for f in knowns_fnames)

        n_sys = len(systems)
        verb("Done")
    elif make_system:
        verb("Constructing systems... ", end='')
        n_sys = args.n_sys
        systems = [construct_system(sysnum, args.n_maxm) \
                   for sysnum in range(n_sys)]
        knowns = (system_known(system) for system in systems)
        verb("Done")


    # Generate data from constructed systems.
    if load_evs:
        verb("Loading EVSs... ", end='')
        EVSs_fname_fmt = outdir + "evs" + os.sep + \
                         "system*.evs.npy.gz"
        EVSs_fnames = sorted([f for f in glob.glob(EVSs_fname_fmt)])
        assert len(systems) == len(EVSs_fnames)
        EVSs = (loadNpy(f) for f in EVSs_fnames)

        n_time = loadNpy(EVSs_fnames[0]).shape[1]
        verb("Lazy")
    elif make_evs:
        verb("Generating EVSs... ", end='')
        n_time = args.n_time
        EVSs = (generate_evs(system, n_time) for system in systems)
        verb("Lazy")


    # Perform estimations on generated data.
    if load_estimated:
        verb("Loading estimations... ", end='')
        estimateds_fname_fmt = outdir + "estimated" + os.sep + \
                              "system*.estimated.npy.gz"
        estimateds_fnames = sorted([f for f in glob.glob(estimateds_fname_fmt)])
        assert len(systems) == len(estimateds_fnames)
        estimateds = (loadNpy(f) for f in estimateds_fnames)
        verb("Lazy")
    elif make_estimated:
        verb("Performing estimations... ", end='')
        estimateds = (estimate_similarities(system, metrics, evs,
                                          n_time) \
                     for system,evs in zip(systems, EVSs))
        verb("Lazy")


    if args.action == "exportcsv":

        verb("Exporting CSVs... ", end='')
        for system,evs,known,estimated in zip(systems,EVSs,knowns,estimateds):
            export_csv_KnownMeasured(system, evs, known, estimated,
                                     n_time, metrics)
        verb("Done")

    elif args.action == "scoreplot":

        # Average scores over systems.
        # 3 is |{ACC, PPV, NPV}|
        fname_scores = outdir + "scores.%s"
        scorespace_names = ["and", "or", "xor", "mix", "lha", "all"]
        scorespace = tuple([] for _ in scorespace_names)

        if load_score:
            verb("Loading scores... ", end='')
            scores_conglomerate = [(nm, loadNpy(fname_scores % nm)) \
                                    for nm in scorespace_names]
            verb("Done")
        elif make_score:
            verb("Scoring metric performance... ", end='')
            # Score how well each metric performed.
            for system,known,estimated in zip(systems,knowns,estimateds):
                compare_scores(system, known, estimated, metrics, scorespace)

            scores_conglomerate = [(nm, np.asarray(scorespace[i])) \
                                    for i,nm in enumerate(scorespace_names)]
            verb("Done")

            verb("Saving scores... ", end='')
            assert np.asarray(scorespace[-1]).shape == (n_sys, len(statNames), nMetrics)
            for nm,scores in scores_conglomerate:
                saveNpy(scores, fname_scores % nm)
            verb("Done")

        verb("Plotting... ", end='')
        plot_scores(metrics, scores_conglomerate)
        verb("Done")


    return 0
# }}} def main

def entryPoint(argv=sys.argv):
    return run(__name__, argv=argv)

if __name__ == "__main__":
    sys.exit(entryPoint())
