#!/usr/bin/env python3

from __future__ import absolute_import, division, print_function

import os
import tensorflow as tf

from dmppl.stats import *

def getDatasets(): # {{{
    # https://www.tensorflow.org/tutorials/load_data/csv

    selectColumns = [
        "known",
        "E[X]",
        "E[Y]",
        "E[X*Y]",
        "E[|X-Y|]",
        "Cls(X,Y)",
        "Cos(X,Y)",
        "Cov(X,Y)",
        "Dep(X,Y)",
        "Ham(X,Y)",
        "Tmt(X,Y)",
    ]

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

    return nInputs, dataset_train, dataset_test
# }}} def getDatasets

def buildModel(nInputs): # {{{
    # nHidden ∈ {0, 2..5}
    nHidden1, nHidden2 = 8, 8

    # act ∈ {sigmoid, relu, tanh}
    #activation1, activation2 = "hard_sigmoid", "hard_sigmoid"
    #activation1, activation2 = "relu", "relu"
    activation1, activation2 = "sigmoid", "sigmoid"
    #activation1, activation2 = "tanh", "tanh"

    useHidden1, useHidden2 = (0 < nHidden1), (0 < nHidden2)

    modelName = "{a1}{n1}_{a2}{n2}".format(
        a1=activation1 if useHidden1 else "",
        n1=nHidden1 if useHidden1 else "I",
        a2=activation2 if useHidden2 else "",
        n2=nHidden2 if useHidden2 else "I",
    )

    inputs = tf.keras.Input(shape=(nInputs,))
    hidden1 = tf.keras.layers.Dense(nHidden1, activation=activation1)(inputs)
    hidden2 = tf.keras.layers.Dense(nHidden2, activation=activation2)(hidden1)

    # NOTE: Output activation should be smooth.
    outputs = tf.keras.layers.Dense(1, activation="sigmoid") \
        (hidden2 if useHidden2 else (hidden1 if useHidden1 else inputs))

    ret = tf.keras.Model(inputs=inputs, outputs=outputs, name=modelName)

    #ret.summary()
    #tf.keras.utils.plot_model(ret, modelName+".png", show_shapes=True)

    return ret
# }}} def buildModel

def fitModel(model, dataset): # {{{

    def customLoss(y_true, y_pred): # {{{
        '''Optimise for BMI and MCC.
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

    #tensorboardDir = os.sep.join(("tensorboard.results", datetime.now().strftime("%Y%m%d-%H%M%S"))),
    tensorboardDir = os.sep.join(("tensorboard.results", model.name))
    # Run tensorboard HTTPD with:
    #   tensorboard --logdir tensorboard.results
    fitCallbacks = [
        tf.keras.callbacks.TensorBoard(log_dir=tensorboardDir),
    ]

    model.compile(loss=fitLoss, optimizer=fitOptimizer, metrics=fitMetrics)

    fitEpochs = 60
    fitStepsPerEpoch = 100

    model.fit(dataset,
              verbose=2, # one line per epoch
              epochs=fitEpochs,
              steps_per_epoch=fitStepsPerEpoch,
              callbacks=fitCallbacks)
# }}} def fitModel

nInputs, dataset_train, dataset_test = getDatasets()

model = buildModel(nInputs)

fitModel(model, dataset_train)

#print(type(dataset_test))
#print(list(dataset_test)[0])
#print(list(dataset_test)[1])

predictions = model.predict(dataset_test)
nPred = 20
for e, k in zip(predictions[:nPred], list(dataset_test)[0][1][:nPred]):
    print(int(k), e[0])

print('EVAL: loss={:0.03f}, acc={:0.03f}, mse={:0.03f}'.format(*model.evaluate(dataset_test)))
