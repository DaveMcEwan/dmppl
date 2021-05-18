
#include <assert.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Specific to this test - File will already be in memory on Taygete.
// 6 char float, 2 char int, newline, return
#define CHARS_PER_LINE (256*7 + 10*2 + 2)
#define DATASET_N_ITEMS (1593)
#define ASCII_LEN (DATASET_N_ITEMS * CHARS_PER_LINE)

#define TOMST_BUFF_N_BYTES 256
#define TINN_N_ITERATIONS 128
#define TINN_BATCH_N_ITEMS 10
#define TINN_MAX_BATCH_N_ITEMS 1024

#define TINN_N_HIDDEN_NEURONS 28
#define TINN_N_BIASES 2
#define TINN_ANNEAL 0.99f

#define DATAITEM_N_INPUT_VALUES 256
#define DATAITEM_N_TARGET_CLASSES 10
typedef struct {
  float in[DATAITEM_N_INPUT_VALUES];
  float tg[DATAITEM_N_TARGET_CLASSES];
} DataItem;

// Computes error.
static float err(const float a, const float b) {
    return 0.5f * (a - b) * (a - b);
}

// Returns partial derivative of error function.
static float pderr(const float a, const float b) {
    return a - b;
}

// Computes total error of target to output.
static float toterr(const float* const tg, const float* const o, const int size) {
    float sum = 0.0f;
    for(int i = 0; i < size; i++)
        sum += err(tg[i], o[i]);
    return sum;
}

// Activation function.
static float act(const float a) {
  return 1.0f / (1.0f + expf(-a));
}

// Returns partial derivative of activation function.
static float pdact(const float a) {
  return a * (1.0f - a);
}

// Returns floating point random from 0.0 - 1.0.
static float frand() {
  int r = rand();
  float fr = ((float)r) / ((float)RAND_MAX);
  return fr;
}

typedef struct {
  float w[TINN_N_HIDDEN_NEURONS * (DATAITEM_N_INPUT_VALUES + DATAITEM_N_TARGET_CLASSES)]; // All the weights.
  float * x; // Hidden to output layer weights.
  float b[TINN_N_BIASES]; // Biases.
  float h[TINN_N_HIDDEN_NEURONS]; // Hidden layer.
  float o[DATAITEM_N_TARGET_CLASSES]; // Output layer.
  int nb; // Number of biases - always two - Tinn only supports a single hidden layer.
  int nw; // Number of weights.
  int nips; // Number of inputs.
  int nhid; // Number of hidden neurons.
  int nops; // Number of outputs.
} Tinn;

// Performs back propagation.
static void bprop (Tinn * t, const float * const in, const float * const tg, float rate) {
  const int nips = t->nips;
  const int nhid = t->nhid;
  const int nops = t->nops;

  for(int i = 0; i < nhid; i++)
  {
    float sum = 0.0f;

    // Calculate total error change with respect to output.
    for(int j = 0; j < nops; j++) {
      const float a = pderr(t->o[j], tg[j]);
      const float b = pdact(t->o[j]);
      sum += a * b * t->x[j * nhid + i];

      // Correct weights in hidden to output layer.
      t->x[j * nhid + i] -= rate * a * b * t->h[i];
    }

    // Correct weights in input to hidden layer.
    for(int j = 0; j < nips; j++) {
      t->w[i * nips + j] -= rate * sum * pdact(t->h[i]) * in[j];
    }
  }
}

// Performs forward propagation.
static void fprop (Tinn * t, const float * const in) {
  const int nips = t->nips;
  const int nhid = t->nhid;
  const int nops = t->nops;

  const float bias_i_to_hid = t->b[0];
  const float bias_hid_to_o = t->b[1];

  // Calculate hidden layer neuron values.
  for(int i = 0; i < nhid; i++) {
    float sum = 0.0f;

    for(int j = 0; j < nips; j++) {
      sum += in[j] * t->w[i * nips + j];
    }

    const float neuron = act(sum + bias_i_to_hid);
    t->h[i] = act(sum + bias_i_to_hid);
  }

  // Calculate output layer neuron values.
  for(int i = 0; i < nops; i++) {
    float sum = 0.0f;

    for(int j = 0; j < nhid; j++) {
      sum += t->h[j] * t->x[i * nhid + j];
    }

    const float neuron = act(sum + bias_hid_to_o);
    t->o[i] = neuron;
  }
}

// Trains a tinn with an input and target output with a learning rate.
// Returns target to output error.
float xttrain (Tinn * t, const float * const in, const float * const tg, float rate) {
  fprop(t, in);
  bprop(t, in, tg, rate);
  return toterr(tg, t->o, t->nops);
}

void initDataSet (DataItem * dataSet) { // {{{

#ifdef TAYGETE
  // ASCII file is prewritten with dma_write().
  char * asciiDataSet = (char *)ASCIIDATASET_ADDR;
#else
  // Put file in buffer as-is.
  char asciiDataSet[ASCII_LEN+1];
  FILE *fd = fopen("semeion.data", "r");
  if (NULL != fd) {
    size_t newLen = fread(asciiDataSet, sizeof(char), ASCII_LEN, fd);
    if (0 != ferror(fd)) {
      printf("error reading file\n");
    } else {
      asciiDataSet[newLen++] = '\0';
    }
    fclose(fd);
  } else {
    assert(false);
  }
#endif


  // First tokenize by newline.
  // strtok modifies asciiDataSet inplace with '0' instead of '\n'.
  char * asciiDataSetLines[DATASET_N_ITEMS];
  for (int row = 0; row < DATASET_N_ITEMS; row++) {
    char * line = strtok(row == 0 ? asciiDataSet : NULL, "\n");
    asciiDataSetLines[row] = line;
  }

  // Cannot put this loop in parallel because strtok relies on sequential calls.

  // Next tokenize by space.
  const int n_cols = DATAITEM_N_INPUT_VALUES + DATAITEM_N_TARGET_CLASSES;
  for (int row = 0; row < DATASET_N_ITEMS; row++) {
    char * asciiDataItemLine = asciiDataSetLines[row];

    for (int col = 0; col < n_cols; col++) {
        const char * num_p = strtok(col == 0 ? asciiDataItemLine : NULL, " ");
        const double vald = strtod(num_p, NULL);
        const float valf = (float)vald;

        if (col < DATAITEM_N_INPUT_VALUES)
          dataSet[row].in[col] = valf;
        else
          dataSet[row].tg[col - DATAITEM_N_INPUT_VALUES] = valf;
    }

  }
  return;
} // }}} initDataSet()

// Replicate xtbuild()
void initTinn (Tinn * t, const int nips, const int nhid, const int nops) { // {{{

  // Tinn only supports one hidden layer so there are 2 biases.
  const int nb = TINN_N_BIASES; // always 2

  const int nw = nhid * (nips + nops);
  t->nb = nb;
  t->nw = nw;
  t->nips = nips;
  t->nhid = nhid;
  t->nops = nops;
  t->x = t->w + nhid * nips;

  // Zero out space for coefficients.
  for (int i = 0; i < nw; i++)   t->w[i] = 0.0f;
  for (int i = 0; i < nb; i++)   t->b[i] = 0.0f;
  for (int i = 0; i < nhid; i++) t->h[i] = 0.0f;
  for (int i = 0; i < nops; i++) t->o[i] = 0.0f;

  // NOTE: Could look for magic value to indicate that pretrained weights are
  // available.
  bool pretrainedAvailable = false;

  // Randomize weights and biases.
  if (!pretrainedAvailable) {
    for (int i = 0; i < nw; i++) t->w[i] = frand() - 0.5f;
    for (int i = 0; i < nb; i++) t->b[i] = frand() - 0.5f;
  }

  return;
} // }}} initTinn()

// Returns an output prediction given an input.
float * xtpredict (Tinn * t, const float * const in) {
  fprop(t, in);
  return t->o;
}

void infer (Tinn * t, volatile DataItem * batch, char * msg) { // {{{
  const int nips = t->nips;
  const int nhid = t->nhid;
  const int nops = t->nops;

  DataItem item = batch[0];

  int d[DATAITEM_N_TARGET_CLASSES]; // fixed at 10 for tinn.
  for (int i = 0; i < DATAITEM_N_TARGET_CLASSES; i++) {
    d[i] = (int)item.tg[i]; // expect tg to be 1.0 or 0.0 only.
  }

  float * p = xtpredict(t, item.in);

  // Find the maximums and compare.
  float tg_maximum = item.tg[0];
  int tg_maximum_idx = 0;
  for (int i = 1; i < nops; i++) {
    if (item.tg[i] > tg_maximum) {
      tg_maximum = item.tg[i];
      tg_maximum_idx = i;
    }
  }
  float pd_maximum = p[0];
  int pd_maximum_idx = 0;
  for (int i = 1; i < nops; i++) {
    if (p[i] > pd_maximum) {
      pd_maximum = p[i];
      pd_maximum_idx = i;
    }
  }

  sprintf(msg, "infer(): %s "
               ": %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f %0.2f"
               " : %d %d %d %d %d %d %d %d %d %d",
          (pd_maximum_idx == tg_maximum_idx) ? "PASS" : "FAIL",
          p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9],
          d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7], d[8], d[9]);
  return;
} // }}} infer()

/**
 Randomly select a number of items from the dataset.
*/
static void prepare_batch (int batch_n_items, int dataset_n_items,
                           DataItem * src, DataItem * dst) { // {{{

  for (int i = 0; i < batch_n_items; i++) {
    int unsigned idx = rand() % dataset_n_items;

    dst[i] = src[idx];
  }
} // }}} prepare_batch()

float train (Tinn * t, volatile DataItem * batch,
            char * msg, uint64_t n_items, float rate) { // {{{
  float error = 0.0f;
  for (uint64_t i = 0; i < n_items; i++) {
    DataItem item = batch[i];

    const float * const in = item.in;
    const float * const tg = item.tg;

    error += xttrain(t, in, tg, rate);
  }
  sprintf(msg, "train(): n_items=%ld rate=%f error=%f", n_items, rate, error);

  return error;
} // }}} train()

//#define DBG_DATASET
int main() {

  DataItem dataSet[DATASET_N_ITEMS];
  initDataSet(dataSet);

  #ifdef DBG_DATASET
  // If data was in this form to begin with it would be 122kB, not 2.9MB.
  for (int i = 0; i < DATASET_N_ITEMS; i++) {
    for (int c = 0; c < DATAITEM_N_INPUT_VALUES/4; c++) {
      float d3 = dataSet[i].in[c*4+0];
      float d2 = dataSet[i].in[c*4+1];
      float d1 = dataSet[i].in[c*4+2];
      float d0 = dataSet[i].in[c*4+3];
      uint8_t d = (d3 == 0.0 ? 0 : 1 << 3)
                | (d2 == 0.0 ? 0 : 1 << 2)
                | (d1 == 0.0 ? 0 : 1 << 1)
                | (d0 == 0.0 ? 0 : 1 << 0);

      printf("%x", d);
    }
    printf(" ");
    for (int c = 0; c < DATAITEM_N_TARGET_CLASSES; c++) {
      float d = dataSet[i].tg[c];
      printf("%d", (int)d);
    }
    printf("\n");
  }
  #endif

  Tinn t;
  initTinn(&t,
           DATAITEM_N_INPUT_VALUES,
           TINN_N_HIDDEN_NEURONS,
           DATAITEM_N_TARGET_CLASSES);

  char msg[TOMST_BUFF_N_BYTES];
  DataItem batchBuff[TINN_MAX_BATCH_N_ITEMS];

  srand(123456);
  float rate = 1.0f;
  const float anneal = TINN_ANNEAL;
  for (int i = 0; i < TINN_N_ITERATIONS-1; i++) {
    prepare_batch(TINN_BATCH_N_ITEMS, DATASET_N_ITEMS, dataSet, batchBuff);
    float error = train(&t, batchBuff, msg, TINN_BATCH_N_ITEMS, rate);
    rate *= anneal;
    printf("iteration %d: rate=%f error=%f <<<%s>>>\n", i, rate, error, msg);
  }

  printf("Testing a few inferences...\n");
  for (int i = 0; i < 20; i++) {
    prepare_batch(1, DATASET_N_ITEMS, dataSet, batchBuff);
    infer(&t, batchBuff, msg);
    printf("inference %d: <<<%s>>>\n", i, msg);
  }

  return 0;
}
