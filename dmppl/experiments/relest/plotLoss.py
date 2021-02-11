
from glob import glob
import os
import numpy as np
import matplotlib.pyplot as plt

from dmppl.base import mkDirP

# CSV fname format:
# <dirCsv> os.sep "run-tf_" <inputCombination> "_" <modelName> "_train-tag-epoch_loss.csv"
dirCsv = "tensorboardCSV"
globPrefix = ''.join((dirCsv, os.sep, "run-tf_"))
globSuffix = "_train-tag-epoch_loss.csv"
globPath = ''.join((
    globPrefix,
    '*', # inputCombination
    "_",
    '*', # modelName
    globSuffix))
fnames = glob(globPath)

def rmPrefix(t, p):
    return t[t.startswith(p) and len(p):]

def rmSuffix(t, s):
    return t[:t.endswith(s) and -len(s)]

names = [rmSuffix(rmPrefix(f, globPrefix), globSuffix) for f in glob(globPath)]
inputCombinations = sorted(list(set(n.split('_', 1)[0] for n in names)))
modelNames = sorted(list(set(n.split('_', 1)[1] for n in names)))
#print(names, len(names))
print(inputCombinations, len(inputCombinations))
print(modelNames, len(modelNames))

colNames = ("Wall time", "Step", "Value")

figsize = (8, 3)
markers = [
    '-k',  # solid line black
    '-b',  # solid line blue
    '-g',  # solid line green
    '-r',  # solid line red
    '-c',  # solid line cyan
    '-m',  # solid line magenta
    '-y',  # solid line yellow
]

dirPlot = dirCsv + ".plots"
mkDirP(dirPlot)
for inputCombination in inputCombinations:
    #csvFnames = {m: globPrefix + inputCombination + '_' + m + globSuffix \
    #    for m in modelNames}
    csvs = {m: \
            np.genfromtxt(globPrefix + inputCombination + '_' + m + globSuffix,
                          delimiter=',',
                          skip_header=1,
                          usecols=(1, 2),
                          unpack=True) \
            for m in modelNames}

    plt.figure(figsize=figsize)
    for i,(m,csv) in enumerate(csvs.items()):
        plt.plot(csv[0], csv[1], label=m)
    plt.legend(loc="lower left", ncol=2)
    plt.xlim(0, 100)
    plt.ylim(-1, 0)
    plt.savefig(dirPlot + os.sep + "relestlearn." + inputCombination + ".pdf",
                bbox_inches="tight")
    plt.close()

