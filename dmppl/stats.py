
from __future__ import absolute_import
from __future__ import division

import numpy as np

# TP, FP, FN, TN are the confusion matrix for binary classifiers.
# True/False Positive/Negative
# https://en.wikipedia.org/wiki/Confusion_matrix
#
# NOTE: These functions are defined to work either with scalars, or with NumPy
# ndarrays in order to calculate many results in one operation.

def truePositiveRate(TP, FP, FN, TN): # {{{
    '''True Positive Rate (Sensitivity, Recall)
    '''
    return TP / (TP + FN)
# }}} truePositiveRate

def trueNegativeRate(TP, FP, FN, TN): # {{{
    '''True Negative Rate (Specificity, Selectivity)
    '''
    return TN / (TN + FP)
# }}} trueNegativeRate

def positivePredictiveValue(TP, FP, FN, TN): # {{{
    '''Positive Predictive Value (Precision)
    '''
    return TP / (TP + FP)
# }}} positivePredictiveValue

def negativePredictiveValue(TP, FP, FN, TN): # {{{
    '''Negative Predictive Value
    '''
    return TN / (TN + FN)
# }}} negativePredictiveValue

def accuracy(TP, FP, FN, TN): # {{{
    '''Accuracy
    '''
    return (TN + TP) / (TN + TP + FN + FP)
# }}} accuracy

def balancedAccuracy(TP, FP, FN, TN): # {{{
    '''Balanced Accuracy
    '''
    tpr = truePositiveRate(TP, FP, FN, TN)
    tnr = trueNegativeRate(TP, FP, FN, TN)
    return (tpr + tnr) / 2
# }}} balancedAccuracy

def matthewsCorrelation(TP, FP, FN, TN): # {{{
    '''Matthews Correlation Coefficient

    https://en.wikipedia.org/wiki/Matthews_correlation_coefficient
    '''
    return (TP*TN - FP*FN) / ((TP+FP) * (TP+FN) * (TN+FP) * (TN+FN))**0.5
# }}} matthewsCorrelation

def bookmakersInformedness(TP, FP, FN, TN): # {{{
    '''Bookmaker's Informedness, Youden's_J_statistic

    https://en.wikipedia.org/wiki/Youden%27s_J_statistic
    '''
    tpr = truePositiveRate(TP, FP, FN, TN)
    tnr = trueNegativeRate(TP, FP, FN, TN)
    return tpr + tnr - 1
# }}} bookmakersInformedness

if __name__ == "__main__":
    assert False, "Not a standalone script."

