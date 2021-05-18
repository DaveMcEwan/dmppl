#ifndef _TINN_TAYGETE
#define _TINN_TAYGETE

/**
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

#include <assert.h>
#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "font8x8_basic.h"

// UST libraries
#include "sysbase.h"
#include "fpga.h"
#include "taygete_msg.h"
#include "si.h"

#define UNUSED(expr) do {(void)(expr);} while (0)

#define TINN_N_HIDDEN_NEURONS 28
#define TINN_N_BIASES 2
#define TINN_ANNEAL 0.99f

#define DATAITEM_N_INPUT_VALUES 256
#define DATAITEM_N_TARGET_CLASSES 10
typedef struct {
  float in[DATAITEM_N_INPUT_VALUES];
  float tg[DATAITEM_N_TARGET_CLASSES];
} DataItem;

/**
    asciiDataSet::ASCII is just semeion.data written to a known location in
    memory at program time.
    dataSet::DataSet must be statically allocated in slave (tinn_taygete.scpu.c).
    Slave calls initDataSet() which fills dataSet with parsed data from
    asciiDataSet.
    Slave also initialises Tinn structure and is the only user.
*/
#define DATASET_N_ITEMS 1593

typedef struct {
  float w[TINN_N_HIDDEN_NEURONS * (DATAITEM_N_INPUT_VALUES + DATAITEM_N_TARGET_CLASSES)]; // All the weights.
  float* x; // Hidden to output layer weights.
  float b[TINN_N_BIASES]; // Biases.
  float h[TINN_N_HIDDEN_NEURONS]; // Hidden layer.
  float o[DATAITEM_N_TARGET_CLASSES]; // Output layer.
  int nb; // Number of biases - always two - Tinn only supports a single hidden layer.
  int nw; // Number of weights.
  int nips; // Number of inputs.
  int nhid; // Number of hidden neurons.
  int nops; // Number of outputs.
} Tinn;



/**
32b address space => 4GiB
Top nibble        => 256MiB
2nd nibble        => 16MiB
3rd nibble        => 1MiB
4th nibble        => 64kiB
5th nibble        => 4kiB
6th nibble        => 256B
7th nibble        => 16B
8th nibble        => 1B

MEMM is 1GiB DRAM in SO-DIMM socket.
SYSM is the Zynq system memmap.

  Address (name) | Use
  -------------- | ---
  0x0*           | -
  0x1*           | -
  0x2*           | -
  0x3*           | -
  0x4* (MEMM)    | Display buffer(?)
  0x5* (MEMM)    | MPU shared data
  0x6* (MEMM)    | ACPU software
  0x7* (MEMM)    | SCPU software
  0x8* (SYSM)    | Zynq PS registers, UST part registers
  0x9* (SYSM)    | Zynq PS registers, UST part registers
  0xA* (SYSM)    |
  0xB* (SYSM)    |
  0xC*           | UST peripherals
  0xD* (SYSM)    |
  0xE* (SYSM)    |
  0xF* (SYSM)    |
*/


/** Inter-Core Communication
Master (MST) is the small RISC-V (Analytics CPU)
Slave (SLV) is the big RISC-V (System CPU)

Slave polls a particular address (TOSLV_CMD) waiting for a command to be placed
there by master.
When slave has started working on the command it will clear the command by
writing 0 to TOMST_REQ.
Slave may use another particular address (TOSLV_BUFFADDR) to find an address of
input data for that command.
When slave has finished working on the command it will place a message in a
buffer and write the location of that buffer to a particular address
(TOMST_BUFFADDR) which will be used by slave.
Once slave has finished working on the command, written a message, and written
the address of the message, it will place a command in a partictular address
(TOMST_REQ) which master may read and act upon before clearing.

Master is not allowed to write TOSLV_* while TOSLV_CMD is not zero, only slave
may clear TOSLV_CMD.
Slave is not allowed to write TOMST_* while TOMST_REQ is not zero, only master
may clear TOMST_REQ.

TOSLV_CMD may be one of the following:
    0                   : No command
    1                   : infer()
    2 | n_items << 8    : train(n_items)
    otherwise           : invalid

TOMST_REQ may be one of the following:
    0                   : No command
    1                   : Report
    otherwise           : invalid

TOSLV_BUFFADDR may be one of the following:
    &(master.c:main():buff0)
    &(master.c:main():buff1)
    otherwise : invalid

TOMST_BUFFADDR may be one of the following:
    &(taygete_scpu.c:main():msg)
    otherwise       : invalid

Usage example:
    Slave waits for master to give a command:
        while (*TOSLV_CMD == 0) {}
    Master commands slave to call infer():
        TOSLV_BUFFADDR = &buff0; // or &buff1
        *TOSLV_CMD = 1
    Master waits for slave to acknowledge command by clearing:
        while (*TOSLV_CMD != 0) {}
    Slave acts upon a command:
        cmd = *TOSLV_CMD & 255;
        arg = *TOSLV_CMD >> 8;
        switch (cmd) {
          1: infer(); break;
          1: train(arg); break;
          default:
            error_unknown_command;
            break;
        }
        *TOSLV_CMD = 0;         // acknowledge command
    Master waits for slave to give a report request:
        while (*TOMST_CMD == 0) {}
    Slave requests master calls report():
        *TOMST_BUFFADDR = &msg;
        *TOMST_REQ = 1;
    Master acts upon a report request:
        if (*TOMST_CMD != 1) error_unknown_request;
        report(*TOMST_BUFFADDR) // print message
        *TOMST_CMD = 0;         // acknowledge request
    Slave waits for master to acknowledge request by clearing:
        while (*TOMST_REQ != 0) {}
    Slave goes back to waiting for command.

Note that the above example is quite inefficient and double buffering can be:
used to give earlier acknowledgements.
*/
// Magic location for each core to signal the host via load/stores.
#define HOSTFLAG_ACPU     ((volatile uint64_t *)  0x50000000)
#define HOSTFLAG_SCPU     ((volatile uint64_t *)  0x50000008)

// Address of Inter-Core Communication flags controlling run state.
#define TOSLV_CMD  ((volatile uint64_t *)0x50001000)
#define TOMST_REQ  ((volatile uint64_t *)0x50001008)

// Address of pointers to message Inter-Core Communication buffers.
// Use like `*TOMST_BUFFADDR = buff0` or `char * buff = *TOMST_BUFFADDR`
#define TOSLV_BUFFADDR    ((DataItem * volatile *)0x50001010)
#define TOMST_BUFFADDR    ((volatile uint64_t *)  0x50001018)
#define TOMST_BINBUFFADDR ((volatile uint64_t *)  0x50001020)

// Report data is variable size, NULL terminated.
// TOMST_BUFFs should be local to ACPU, within (0x60000000-0x6fffffff)
#define TOMST_BUFF_N_BYTES 256

// ASCII data loaded into memory separately at known address.
#define ASCIIDATASET_ADDR   ((char *)0x51000000)

// UltraSoC peripherals.
#define TAYGETE_AXI_COMMUNICATOR    ((volatile uint64_t *)0xC0000000)
#define TAYGETE_STATIC_INSTR        ((volatile uint64_t *)0xC0010000)
#define TAYGETE_VIRTUAL_CONSOLE     ((volatile uint64_t *)0xC0020000)


// When instrumenting wait a bit longer between polls to prevent flooding buffer
// with useless get_addr enter/exit times.
#ifdef UST_SI
#  define POLL_DELAY 1000000
#else
#  define POLL_DELAY 10
#endif

/**
 Retrieve the value at a given address.
*/
uint64_t __attribute__ ((noinline)) get_addr (volatile uint64_t * addr) { // {{{
  _flush_dcache();
  return *addr;
} // }}} get_addr()

/**
 Set a given address to a given value.
*/
void __attribute__ ((noinline)) set_addr (volatile uint64_t * addr, uint64_t v) { // {{{
  *addr = v;
  _flush_dcache();
  return;
} // }}} set_addr()

/**
 Poll while value at given address is equal to given value.
*/
uint64_t __attribute__ ((noinline)) wait_while (volatile uint64_t * addr, uint64_t m) { // {{{

  volatile uint64_t v = get_addr(addr);
  while (v == m) {
    _delay_cycles(POLL_DELAY);
    v = get_addr(addr);
  }

  return v;
} // }}} wait_while()

/**
 Poll until value at given address is equal to given value.
*/
uint64_t __attribute__ ((noinline)) wait_until (volatile uint64_t * addr, uint64_t m) { // {{{

  volatile uint64_t v = get_addr(addr);
  while (v != m) {
    _delay_cycles(POLL_DELAY);
    v = get_addr(addr);
  }

  return v;
} // }}} wait_until()


#define LCD_WIDTH           800
#define LCD_HEIGHT          480
#define LCD_PIXEL_BYTES     4
#define COLOR_BLACK     0x00000000
#define COLOR_RED       0x000000FF
#define COLOR_GREEN     0x0000FF00
#define COLOR_BLUE      0x00FF0000
#define COLOR_YELLOW    0x0000FFFF
#define COLOR_MAGENTA   0x00FF00FF
#define COLOR_CYAN      0x00FFFF00
#define COLOR_WHITE     0x00FFFFFF
#define COLOR_UOBMAROON 0x002E1CB0
#define COLOR_USTORANGE 0x001A67C0

/**
 Draw ASCII character to screen.
*/
void draw_char(const char c, const int x, const int y, const int color) { // {{{
    assert(c < 0x7F);
    char * bitmap = font8x8_basic[(int)c];

    const int sc_x = 1;
    const int sc_y = 2;

    for (int row = 0; row < 8; row++) {
      for (int col = 0; col < 8; col++) {

        if (bitmap[row] & (1 << col)) {
          draw_block(x + col*sc_x, y + row*sc_y,
                     sc_x,sc_y,
                     color);
        }

      }
    }

} // }}} draw_char()

/**
 Draw string of ASCII characters to screen.
*/
void draw_string(const int x, const int y, const char * s, const int color) { // {{{
  const int char_w = 8;

  int i = 0;
  char c;
  while ((c = s[i++])) {
    draw_char(c, x+i*char_w, y, color);
  }

} // }}} draw_string()

#endif // _TINN_TAYGETE
