#!/usr/bin/env python3

from __future__ import absolute_import, division, print_function

import os
import tensorflow as tf
import itertools
from contextlib import redirect_stdout

from dmppl.base import *
from dmppl.stats import *

# Goal is to make 2 models.
# 1. GoalBetter, aiming for better metric, using all existing metrics as input.
#    plus_sigm8_sigm8
#    Can be made to give cycle-by-cycle estimates (slightly delayed realtime).
# 2. GoalMin, minimum calculation to compete with Cov, Dep, etc

sweepNotChosen = False

# NOTE: In `components`, sigmoid/hard_sigmoid makes a difference.
chosenModelParams = (
    (2, "hard_sigmoid", 0, "hard_sigmoid"), # hard2_hard0
    (4, "hard_sigmoid", 0, "hard_sigmoid"), # hard4_hard0
    (8, "hard_sigmoid", 0, "hard_sigmoid"), # hard8_hard0
    (4, "hard_sigmoid", 4, "hard_sigmoid"), # hard4_hard4
    (8, "hard_sigmoid", 8, "hard_sigmoid"), # hard8_hard8
    (8, "sigmoid",      8, "sigmoid"),      # sigm8_sigm8
    (8, "relu",         8, "relu"),         # relu8_relu8
    (8, "tanh",         8, "tanh"),         # tanh8_tanh8
)

# Use sweepModelParams to sweep a selection of model parameters.
# 5*4*5*4=400 models
numbers, activations = \
    (0, 2, 4, 8, 16), \
    ("hard_sigmoid", "sigmoid", "relu", "tanh")
sweepModelParams = list(itertools.product((numbers, activations, numbers, activations)))

inputCombinations = {
    "assisted": ["E[X]", "E[Y]", "E[X*Y]", "E[|X-Y|]", "Cls(X,Y)", "Cos(X,Y)",
                 "Cov(X,Y)", "Dep(X,Y)", "Ham(X,Y)", "Tmt(X,Y)"],
    "perfcntrs": ["E[X]", "E[Y]", "E[X*Y]", "E[|X-Y|]"],
}

defaultLogdir = "tf.results"

def getDatasets(**kwargs): # {{{
    # https://www.tensorflow.org/tutorials/load_data/csv

    inputCombination = kwargs.get("selectColumns", "assisted")
    selectColumns = ["known"] + inputCombinations[inputCombination]

    # NOTE: make_csv_dataset is experimental. Look out for API change.
    # NOTE: Reader is very strict! Can't cope with multi-char delimiter.

    raw_dataset_train = tf.data.experimental.make_csv_dataset(
        "combinedTrain.csv",
        batch_size=64,
        label_name="known", # NOTE: Must be in `select_columns`
        select_columns=selectColumns,
        shuffle=True,
        sloppy=True, # Sloppy --> Non-deterministic
        num_epochs=-1, # Infinitely repeating dataset
    )

    raw_dataset_test = tf.data.experimental.make_csv_dataset(
        "combinedTest.csv",
        batch_size=64,
        label_name="known", # NOTE: Must be in `select_columns`
        select_columns=selectColumns,
        shuffle=False,
        sloppy=False, # Non-sloppy --> deterministic
        num_epochs=1, # Not infinitely repeating dataset
    )

    def showBatch(batch): # {{{
        for k, v in batch.items():
            print("{:20s}: {}".format(k, v.numpy()))
    # }}} def showBatch

    def pack(features, label): # {{{
        return tf.stack(list(features.values()), axis=-1), label
    # }}} def pack

    packed_dataset_train = raw_dataset_train.map(pack)
    packed_dataset_test = raw_dataset_test.map(pack)

    # Do additional shuffling here.
    dataset_train = packed_dataset_train
    dataset_test = packed_dataset_test

    nInputs = len(selectColumns)-1

    logdir = '.'.join((inputCombination, "results"))
    mkDirP(logdir)

    return nInputs, logdir, dataset_train, dataset_test
# }}} def getDatasets

def buildModel(nInputs, **kwargs): # {{{

    # n ∈ {0, 2, 4, 8, 16}
    n1, n2 = kwargs.get("n1", 8), kwargs.get("n2", 8)

    # a ∈ {sigmoid, relu, tanh}
    a1, a2 = kwargs.get("a1", "hard_sigmoid"), kwargs.get("a2", "hard_sigmoid")

    useHidden1, useHidden2 = (0 < n1), (0 < n2)

    modelName = "{a1}{n1}_{a2}{n2}".format(
        a1=a1[:4] if useHidden1 else "",
        n1=n1,
        a2=a2[:4] if useHidden2 else "",
        n2=n2,
    )

    inputs = tf.keras.Input(shape=(nInputs,))
    hidden1 = tf.keras.layers.Dense(n1, activation=a1)(inputs)
    hidden2 = tf.keras.layers.Dense(n2, activation=a2)(hidden1)

    # NOTE: Output activation should be smooth.
    outputs = tf.keras.layers.Dense(1, activation="sigmoid") \
        (hidden2 if useHidden2 else (hidden1 if useHidden1 else inputs))

    model = tf.keras.Model(inputs=inputs, outputs=outputs, name=modelName)

    logdir = kwargs.get("logdir", defaultLogdir)
    fnameTxt = joinP(logdir, modelName+".txt")
    fnamePng = joinP(logdir, modelName+".png")

    with open(fnameTxt, 'w') as fd:
        with redirect_stdout(fd):
            model.summary()

    tf.keras.utils.plot_model(model, to_file=fnamePng, show_shapes=True)

    return model
# }}} def buildModel

def fitModel(model, dataset, **kwargs): # {{{

    def customLoss(y_true, y_pred): # {{{
        '''Optimise against BMI.
        '''
        y_true = tf.keras.backend.cast_to_floatx(y_true)
        y_pred = tf.keras.backend.cast_to_floatx(y_pred)

        def truePositive(y_true, y_pred):
            return tf.keras.backend.sum(y_true * y_pred)

        def falsePositive(y_true, y_pred):
            return tf.keras.backend.sum((1-y_true) * y_pred)

        def falseNegative(y_true, y_pred):
            return tf.keras.backend.sum(y_true * (1-y_pred))

        def trueNegative(y_true, y_pred):
            return tf.keras.backend.sum((1-y_true) * (1-y_pred))

        tp, fp, tn, fn = \
            truePositive(y_pred, y_true), \
            falsePositive(y_pred, y_true), \
            trueNegative(y_pred, y_true), \
            falseNegative(y_pred, y_true)

        gain = bookmakersInformedness(tp, fp, fn, tn)

        return gain * -1
    # }}} def customLoss

    #fitLoss = "binary_crossentropy"
    fitLoss = customLoss

    fitOptimizer = tf.keras.optimizers.Adam(learning_rate=0.001, amsgrad=True, clipnorm=1.0, clipvalue=1.0)
    #fitOptimizer = tf.keras.optimizers.Nadam()
    #fitOptimizer = tf.keras.optimizers.Adadelta()
    #fitOptimizer = tf.keras.optimizers.SGD()

    fitMetrics = [
        "acc", # accuracy
        "mse", # mean squared error
    ]

    logdir = kwargs.get("logdir", defaultLogdir)
    tensorboardDir = joinP(logdir, "tf", model.name)

    # Run tensorboard HTTPD with:
    #   tensorboard --logdir tf.results
    fitCallbacks = [
        tf.keras.callbacks.TensorBoard(log_dir=tensorboardDir),
    ]

    model.compile(loss=fitLoss, optimizer=fitOptimizer, metrics=fitMetrics)

    fitEpochs = 100
    fitStepsPerEpoch = 100

    model.fit(dataset,
              verbose=0, # silent
              #verbose=2, # one line per epoch
              epochs=fitEpochs,
              steps_per_epoch=fitStepsPerEpoch,
              callbacks=fitCallbacks)
# }}} def fitModel

modelParams = sweepModelParams if sweepNotChosen else chosenModelParams

for inputCombination in inputCombinations.keys():

    nInputs, logdir, dataset_train, dataset_test = \
        getDatasets(selectColumns=inputCombination)

    for i,(n1,a1,n2,a2) in enumerate(modelParams):

        model = buildModel(nInputs, n1=n1, a1=a1, n2=n2, a2=a2, logdir=logdir)

        fitModel(model, dataset_train, logdir=logdir)

        loss, acc, mse = model.evaluate(dataset_test)

        fnameTxt = joinP(logdir, model.name+".txt")
        with open(fnameTxt, 'a') as fd:
            with redirect_stdout(fd):
                print(' '.join((
                    "EVAL",
                    str(i),
                    model.name,
                    "loss=%0.04f" % loss,
                    "acc=%0.04f" % acc,
                    "mse=%0.04f" % mse,
                )))

#predictions = model.predict(dataset_test)
#nPred = 20
#for e, k in zip(predictions[:nPred], list(dataset_test)[0][1][:nPred]):
#    print(int(k), e[0])
#
#print('EVAL: loss={:0.03f}, acc={:0.03f}, mse={:0.03f}'.format(*model.evaluate(dataset_test)))
