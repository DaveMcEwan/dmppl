
/**
Analytics CPU (RV64IM) part of TINN on UltraSoC Taygete system.
Display results produced by SCPU.

MIT License

Copyright (c) 2019 Dave McEwan

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

#define TINN_N_ITERATIONS 128
#define TINN_BATCH_N_ITEMS 100
#define TINN_MAX_BATCH_N_ITEMS 1024

/**
 Randomly select a number of items from the dataset.
*/
void prepare_batch (int batch_n_items, int dataset_n_items,
                           DataItem src[], DataItem dst[]) { // {{{

  for (int i = 0; i < batch_n_items; i++) {
    int idx = rand() % dataset_n_items;

    dst[i] = src[idx];
  }
} // }}} prepare_batch()

/**
 Draw handwritten digit to screen.
*/
void draw_semeion_digit(const int index, const DataItem * item) { // {{{
    const int base_x = 70*(index % 10);
    const int base_y = 20;
    const int item_w = 16;
    const int item_h = 16;
    const int data_margin = 3;
    const int sc = 4;

    // Clear input data background.
    draw_block(base_x+data_margin, base_y+data_margin,
               item_w*sc, item_h*sc, // 64x64
               COLOR_WHITE);

    #ifdef VC_DISPLAY
    printf("+----------+\n");
    #endif
    for (int row = 0; row < item_h; row++) {
      for (int col = 0; col < item_w; col++) {
        int i = row*item_w + col;

        assert(i < 256);
        assert(0.0 <= item->in[i]);
        assert(item->in[i] <= 1.0);
        assert(item->in[i] == 0.0 || item->in[i] == 1.0);
        #ifdef VC_DISPLAY
        printf(item->in[i] == 1.0 ? "#" : " ");
    #endif

        const int darkness = 255 - (int)(255 * item->in[i]);
        assert(darkness==0 || darkness==255);

        const int pixcolor = darkness << 16 | darkness << 8 | darkness;
        assert(pixcolor==COLOR_BLACK || pixcolor==COLOR_WHITE);

        if (pixcolor != COLOR_WHITE) {
          draw_block(base_x+data_margin + col*sc, base_y+data_margin + row*sc,
                     sc,sc, // 4x4
                     pixcolor);
        }
      }
    #ifdef VC_DISPLAY
      printf("|\n");
    #endif
    }
    #ifdef VC_DISPLAY
    printf("+----------+\n");
    #endif

    // Clear histogram background.
    draw_block(base_x+5,base_y+80, 60,100, COLOR_WHITE);
    #ifdef VC_DISPLAY
    printf("%6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f\n",
           item->tg[0], item->tg[1],
           item->tg[2], item->tg[3],
           item->tg[4], item->tg[5],
           item->tg[6], item->tg[7],
           item->tg[8], item->tg[9]);
    #endif

    for (int i = 0; i < 10; i++) {
      if (item->tg[i] != 0.0) {
        draw_block(base_x+5 + i*6, base_y+80,
                   6,(int)(100*item->tg[i]),
                   COLOR_RED);
      }
    }

} // }}} draw_semeion_digit()

/**
 Draw infer() result to screen.
*/
void draw_infer_result(const int index, const float * result) { // {{{
    const int base_x = 70*(index % 10);
    const int base_y = 20;
    const int bar_w = 6;
    const int max_bar_h = 100;

    for (int i = 0; i < 10; i++) {
      const int bar_h = (int)(max_bar_h*result[i]);

      draw_block(base_x+5 + i*bar_w, base_y+80+(max_bar_h-bar_h),
                 bar_w,bar_h,
                 COLOR_BLUE);
    }

} // }}} draw_infer_result()

/**
 Read local buffer and report the results.
*/
void report (float binmsg[], char * msg, int index, bool use_binmsg) { // {{{
  if (use_binmsg) {
    draw_infer_result(index, binmsg);

    //#ifdef EXTRA_PRINTF
    //printf("report():binmsg "
    //       "%6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f\n",
    //       binmsg[0], binmsg[1], binmsg[2], binmsg[3], binmsg[4],
    //       binmsg[5], binmsg[6], binmsg[7], binmsg[8], binmsg[9]);
    //#endif
  }

  // printf is wrapped to use virtual console by UltraSoC's sys_wrappers.c
  printf("REPORT (%d) <<<%s>>>\n", index, msg);
} // }}}

/**
 Analytics CPU main.
*/
int main () { // {{{
  #ifdef EXTRA_PRINTF
  printf("ACPU main()\n");
  #endif

  draw_block(0,0, LCD_WIDTH,LCD_HEIGHT/2, COLOR_UOBMAROON);
  set_addr(HOSTFLAG_ACPU, 0);

  srand(1618034); // Seed with golden ratio.

  // Master will not start until slave initiates a command.
  set_addr(TOSLV_CMD, 0);

  // Wait for slave to indicate the dataset is initialized.
  wait_until(TOMST_REQ, 123);
  set_addr(TOMST_REQ, 0); // Acknowledge

  int unsigned currentBuff = 0;
  DataItem * dataSet = (DataItem *)get_addr(TOMST_BUFFADDR);
  DataItem buff0[TINN_MAX_BATCH_N_ITEMS];
  DataItem buff1[TINN_MAX_BATCH_N_ITEMS];
  float localBinMsg[DATAITEM_N_TARGET_CLASSES];
  char localMsg[TOMST_BUFF_N_BYTES];

  char drawmsg[32];

  int batch_n_items = TINN_BATCH_N_ITEMS;

  // Command slave to train its NN.
  prepare_batch(batch_n_items, DATASET_N_ITEMS,
                dataSet, (currentBuff ? buff1 : buff0));
  *TOSLV_BUFFADDR = (currentBuff ? buff1 : buff0);
  set_addr(TOSLV_CMD, (2 | (batch_n_items << 8))); // TRAIN

  for (int i = 0; i < TINN_N_ITERATIONS-1; i++) {
    draw_block(710,20, 80,200, COLOR_BLACK);
    sprintf(drawmsg, "TRAINING"); draw_string(710,25, drawmsg, COLOR_WHITE);
    sprintf(drawmsg, "batches:"); draw_string(710,45, drawmsg, COLOR_WHITE);
    sprintf(drawmsg, "%d", i); draw_string(710,65, drawmsg, COLOR_WHITE);
    sprintf(drawmsg, "items:"); draw_string(710,85, drawmsg, COLOR_WHITE);
    sprintf(drawmsg, "%d", i*TINN_BATCH_N_ITEMS); draw_string(710,105, drawmsg, COLOR_WHITE);

    // Put next input in place once slave starts analysing current.
    currentBuff ^= 1;
    prepare_batch(batch_n_items, DATASET_N_ITEMS,
                  dataSet, (currentBuff ? buff1 : buff0));
    wait_until(TOSLV_CMD, 0);

    *TOSLV_BUFFADDR = (currentBuff ? buff1 : buff0);
    set_addr(TOSLV_CMD, (2 | (batch_n_items << 8))); // TRAIN

    // Draw the first item in the batch just to show something is happening.
    draw_semeion_digit(i, &((currentBuff ? buff1 : buff0)[0]));

    // Poll for slave to finish processing.
    wait_while(TOMST_REQ, 0);

    // Take a local copy of the result and allow slave to do something else.
    strncpy((char *)localMsg, (char *)*TOMST_BUFFADDR, TOMST_BUFF_N_BYTES);
    set_addr(TOMST_REQ, 0);

    // Display result on UART/screen.
    report(localBinMsg, localMsg, i, false);
    set_addr(HOSTFLAG_ACPU, i);
  }

  #ifdef EXTRA_PRINTF
  printf("Training stopped after %d iterations.\n", TINN_N_ITERATIONS);
  printf("Starting inference.\n");
  #endif

  int infer_cntr = 0;

  draw_block(710,20, 80,200, COLOR_BLACK);
  draw_string(710,25, "PREDICT", COLOR_WHITE);
  draw_string(710,45, "items:", COLOR_WHITE);
  sprintf(drawmsg, "%d", infer_cntr); draw_string(710,65, drawmsg, COLOR_WHITE);

  // NN is now trained so just perform inference forever.
  prepare_batch(1, DATASET_N_ITEMS, dataSet, (currentBuff ? buff1 : buff0));
  *TOSLV_BUFFADDR = (currentBuff ? buff1 : buff0);
  set_addr(TOSLV_CMD, 1); // INFER

  // Display input data.
  draw_semeion_digit(infer_cntr++, &((currentBuff ? buff1 : buff0)[0]));

  while (1) {
    draw_block(710,65, 80,20, COLOR_BLACK);
    sprintf(drawmsg, "%d", infer_cntr); draw_string(710,65, drawmsg, COLOR_WHITE);

    // Put next input in place once slave starts analysing current.
    currentBuff ^= 1;
    prepare_batch(1, DATASET_N_ITEMS, dataSet, (currentBuff ? buff1 : buff0));
    *TOSLV_BUFFADDR = (currentBuff ? buff1 : buff0);
    wait_until(TOSLV_CMD, 0);

    *TOSLV_BUFFADDR = (currentBuff ? buff1 : buff0);
    set_addr(TOSLV_CMD, 1); // INFER

    // Display input data.
    draw_semeion_digit(infer_cntr, &((currentBuff ? buff1 : buff0)[0]));

    // Poll for slave to finish processing.
    wait_while(TOMST_REQ, 0);

    // Take a local copy of the result and allow slave to do something else.
    for (int i = 0; i < DATAITEM_N_TARGET_CLASSES; i++) {
      localBinMsg[i] = ((float *)*TOMST_BINBUFFADDR)[i];
    }
    strncpy((char *)localMsg, (char *)*TOMST_BUFFADDR, TOMST_BUFF_N_BYTES);
    set_addr(TOMST_REQ, 0);

    // Display result on UART/screen.
    report(localBinMsg, localMsg, infer_cntr-1, true);
    set_addr(HOSTFLAG_ACPU, infer_cntr-1);

    #ifdef HUMAN_VISUAL_DELAY
    delay_us(500000);
    #endif

    infer_cntr++;
  }

  assert(false);
  return -1;
} // }}} main()

