
/**
System CPU (RV64IMAFD) part of TINN on UltraSoC Taygete system.
Compute interesting results for ACPU to display.

Based on https://github.com/glouw/tinn

MIT License

Copyright (c) 2019 Dave McEwan
Copyright (c) 2018 Gustav Louw

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

#include "tinn.h"

// {{{ tinn original functions

// Avoid instrumenting very simple and frequently called functionsl to prevent
// instrumentation buffer clogging up.
// When the UST Message Engine and the USB interface are clogged there is the
// knock-on effect of the AXI bus being stalled so everything slows down and
// eventually fails.

// Computes error.
__attribute__ ((no_instrument_function))
static float err(const float a, const float b) {
  return 0.5f * (a - b) * (a - b);
}

// Computes total error of target to output.
static float toterr(const float* const tg, const float* const o, const int size) {
  float sum = 0.0f;
  for(int i = 0; i < size; i++)
    sum += err(tg[i], o[i]);
  return sum;
}

// Activation function.
__attribute__ ((no_instrument_function))
static float act(const float a) {
  return 1.0f / (1.0f + expf(-a));
}

// Returns partial derivative of activation function.
__attribute__ ((no_instrument_function))
static float pdact(const float a) {
  return a * (1.0f - a);
}

// Returns floating point random from 0.0 - 1.0.
static float frand() {
  int r = rand();
  float fr = ((float)r) / ((float)RAND_MAX);
  return fr;
}

// Performs back propagation.
static void bprop (Tinn * t, const float * const in, const float * const tg, const float rate) {
  const int nips = t->nips;
  const int nhid = t->nhid;
  const int nops = t->nops;

  for(int i = 0; i < nhid; i++)
  {
    float sum = 0.0f;

    // Calculate total error change with respect to output.
    for(int j = 0; j < nops; j++) {
      const float a = t->o[j] - tg[j];
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
    t->h[i] = neuron;
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

// Returns an output prediction given an input.
static float * xtpredict (Tinn * t, const float * const in) {
  fprop(t, in);
  return t->o;
}

// Trains a tinn with an input and target output with a learning rate.
// Returns target to output error.
static float xttrain (Tinn * t, const float * const in, const float * const tg, const float rate) {
  fprop(t, in);
  bprop(t, in, tg, rate);
  return toterr(tg, t->o, t->nops);
}

// }}} tinn original functions

/**
 Initialize dataSet by reading in semeion.data text file.
*/
void initDataSet (DataItem dataSet[]) { // {{{

  // ASCII file is prewritten with dma_write().
  char * asciiDataSet = (char *)ASCIIDATASET_ADDR;

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

        if (col < DATAITEM_N_INPUT_VALUES) {
          dataSet[row].in[col] = valf;
          assert(0.0 <= valf);
          assert(valf <= 1.0);
        }
        else {
          dataSet[row].tg[col - DATAITEM_N_INPUT_VALUES] = valf;
          assert(valf==0.0 || valf==1.0);
        }
    }

  }
  return;
} // }}} initDataSet()

/**
 Draw visualization of Tinn weights to screen.
*/
void draw_tinn(const Tinn * t) { // {{{
  const int sc_x = 2;
  const int sc_y = 4;

  int base_x = 44;
  int base_y = LCD_HEIGHT/2 + 44;

  // Weights between input layer and hidden layer.
  for (int row = 0; row < TINN_N_HIDDEN_NEURONS; row++) {
    for (int col = 0; col < DATAITEM_N_INPUT_VALUES; col++) {
      const int i = row*DATAITEM_N_INPUT_VALUES + col;
      const float w = t->w[i];

      const int darkness = 255 - (int)(255 * w);

      const int pixcolor = darkness << 16 | darkness << 8 | darkness;

      draw_block(base_x + col*sc_x, base_y + row*sc_y,
                 sc_x, sc_y,
                 pixcolor);
    }
  }

  base_x += base_x + sc_x*DATAITEM_N_INPUT_VALUES;

  // Weights between input layer and hidden layer.
  for (int row = 0; row < DATAITEM_N_TARGET_CLASSES; row++) {
    for (int col = 0; col < TINN_N_HIDDEN_NEURONS; col++) {
      const int i = row*TINN_N_HIDDEN_NEURONS + col;
      const float w = t->x[i];

      const int darkness = 255 - (int)(255 * w);

      const int pixcolor = darkness << 16 | darkness << 8 | darkness;

      draw_block(base_x + col*sc_x, base_y + row*sc_y,
                 sc_x, sc_y,
                 pixcolor);
    }
  }

} // }}} draw_tinn()

/**
 Initialize Tinn structure. Similar to xtbuild().
*/
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

  draw_tinn(t);

  return;
} // }}} initTinn()

/**
 Infer the most estimated probability of the first item in a batch belonging to
 each target class.
*/
void infer (Tinn * t, const DataItem batch[], char * msg, float binmsg[]) { // {{{
  const int nips = t->nips; UNUSED(nips);
  const int nhid = t->nhid; UNUSED(nhid);
  const int nops = t->nops;

  const DataItem item = batch[0];

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

  for (int i = 0; i < DATAITEM_N_TARGET_CLASSES; i++) {
    binmsg[i] = p[i];
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
 Train with a batch of a given size at a given rate.
*/
float train (Tinn * t, const DataItem batch[], char * msg, const int n_items, const float rate) { // {{{
  static int cum_items = 0;

  float error = 0.0f;
  for (int i = 0; i < n_items; i++) {
    const DataItem item = batch[i];

    const float * const in = item.in;
    const float * const tg = item.tg;

    error += xttrain(t, in, tg, rate);
  }

  cum_items += n_items;

  // Convert floats to ints to avoid weirdness with printing.
  //int rate_int = (int)(rate * 10000);
  //int error_int = (int)(error);

  draw_block(0,460, 800,20, COLOR_USTORANGE);
  sprintf(msg, "rate=%f error=%f%% cum_items=%d", rate, error, cum_items);
  draw_string(20,460, msg, COLOR_WHITE);
  draw_tinn(t);
  sprintf(msg, "train(): n_items=%d rate=%f error=%f%%", n_items, rate, error);

  return error;
} // }}} train()

/**
 System CPU main.
*/
int main () { // {{{
  #ifdef EXTRA_PRINTF
  printf("SCPU main()\n");
  #endif

  draw_block(0,LCD_HEIGHT/2, LCD_WIDTH,LCD_HEIGHT/2, COLOR_USTORANGE);

  srand(3141593); // Seed with pi.

  set_addr(TOMST_REQ, 0);

  Tinn t;
  #ifdef EXTRA_PRINTF
  printf("initTinn() &t=%p... ", &t);
  #endif
  initTinn(&t,
           DATAITEM_N_INPUT_VALUES,
           TINN_N_HIDDEN_NEURONS,
           DATAITEM_N_TARGET_CLASSES);
  #ifdef EXTRA_PRINTF
  printf("DONE\n");
  #endif

  DataItem dataSet[DATASET_N_ITEMS];
  #ifdef EXTRA_PRINTF
  printf("initDataSet() &(dataSet[0])=%p... ", &(dataSet[0]));
  #endif
  initDataSet(dataSet);
  set_addr(TOMST_BUFFADDR, (uint64_t)&dataSet);
  #ifdef EXTRA_PRINTF
  printf("DONE\n");
  #endif

  // No assumptions about which core is ready to interact first.
  // Master will wait for magic value indicating that dataset is initialized.
  set_addr(TOMST_REQ, 123);
  #ifdef EXTRA_PRINTF
  printf("Slave (SCPU) ready\n");
  #endif

  char msg[TOMST_BUFF_N_BYTES];
  float binmsg[DATAITEM_N_TARGET_CLASSES];

  float rate = 1.0f;
  const float anneal = TINN_ANNEAL;

  while (1) {

    // Wait for command
    uint64_t rawcmd = wait_while(TOSLV_CMD, 0);

    // Received command, take copy and acknowledge.
    uint64_t cmd = rawcmd & 255;
    uint64_t arg = rawcmd >> 8; UNUSED(arg);
    set_addr(TOSLV_CMD, 0);

    // Perform work and write message to buffer.
    switch (cmd) {
      case 1:
        #ifdef EXTRA_PRINTF
        printf("infer()...");
        #endif
        infer(&t, *TOSLV_BUFFADDR, msg, binmsg);
        #ifdef EXTRA_PRINTF
        printf("DONE\n");
        #endif
        break;
      case 2:
        #ifdef EXTRA_PRINTF
        printf("train()...");
        #endif
        train(&t, *TOSLV_BUFFADDR, msg, arg, rate);
        rate *= anneal;
        #ifdef EXTRA_PRINTF
        printf("DONE\n");
        #endif
        break;
      default:
        // error_unknown_command;
        break;
    }

    // Wait for master to finish with previous message.
    // This should not happen often.
    wait_until(TOMST_REQ, 0);

    // Point master to buffer and make request.
    set_addr(TOMST_BUFFADDR, (uint64_t)msg);
    set_addr(TOMST_BINBUFFADDR, (uint64_t)binmsg);
    set_addr(TOMST_REQ, 1);
  }

  assert(false);
  return -1;
} // }}}

