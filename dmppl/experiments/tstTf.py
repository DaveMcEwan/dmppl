from __future__ import absolute_import, division, print_function

import tensorflow as tf

defaultColumns = [
    "known",
    "E[X]",
    "E[Y]",
    "E[X*Y]",
    "E[|X-Y|]",
    #"Cos(X,Y)",
]

# https://www.tensorflow.org/tutorials/load_data/csv
def getDataset(fname, **kwargs): # {{{

    # NOTE: make_csv_dataset is experimental. Look out for API change.
    # NOTE: Reader is very strict! Can't cope with multi-char delimiter.
    return tf.data.experimental.make_csv_dataset(
        fname,
        batch_size=256,
        label_name="known", # NOTE: Must be in `select_columns`
        select_columns=kwargs.get("columns", defaultColumns),
        shuffle=True,
        sloppy=False, # Non-sloppy --> deterministic
        num_epochs=1, # Not infinitely repeating dataset
    )
# }}} def getDataset

def showBatch(batch): # {{{
    for k, v in batch.items():
        print("{:20s}: {}".format(k, v.numpy()))
# }}} def showBatch

datasetTrain = getDataset("combined.csv")
datasetTest = getDataset("combined.csv") # TODO: Split these

# TODO: Pack items into inputs
def pack(features, label): # {{{
    return tf.stack(list(features.values()), axis=-1), label
# }}} def pack

packedDatasetTrain = datasetTrain.map(pack)
packedDatasetTest = datasetTest.map(pack)

# nHidden ∈ {0, 2..5}
# act ∈ {sigmoid, relu, tanh} # TODO: hard_sigmoid instead of sigmoid?
nHidden1 = 0
nHidden2 = 0
act1 = "hard_sigmoid"
act2 = "relu"
modelName = "{act1}{nHidden1}_{act2}{nHidden2}".format(
    act1=act1 if 0 < nHidden1 else "",
    nHidden1=nHidden1 if 0 < nHidden1 else "NONE",
    act2=act2 if 0 < nHidden2 else "",
    nHidden2=nHidden2 if 0 < nHidden2 else "NONE",
)

assert nHidden1 >= nHidden2

inputs = tf.keras.Input(shape=(len(defaultColumns)-1,))
hidden1 = tf.keras.layers.Dense(nHidden1, activation=act1)(inputs)
hidden2 = tf.keras.layers.Dense(nHidden2, activation=act2)(hidden1)
outputs = tf.keras.layers.Dense(1, activation="hard_sigmoid") \
    (hidden2 if 0 < nHidden2 else (hidden1 if 0 < nHidden1 else inputs))

model = tf.keras.Model(inputs=inputs, outputs=outputs, name=modelName)

model.summary()
tf.keras.utils.plot_model(model, modelName+".png", show_shapes=True)

modelLoss = "binary_crossentropy"
modelOptimizer = "adam"
modelMetrics = ["accuracy"]
model.compile(loss=modelLoss, optimizer=modelOptimizer, metrics=modelMetrics)

model.fit(packedDatasetTrain, epochs=20)
