
// UltraSoC Static Instrumentation via GCC

/**
 GCC options for compiling with debug symbols (-g) and inserting wrappers around
 all functions (-finstrument-functions) require these wrappers to be defined.
 ACPU.enter     8
 ACPU.exit      9
 SCPU.enter     10
 SCPU.exit      11
*/
#define SI_BASE 0xC0010000l

#ifdef __cplusplus
extern "C"
#endif
__attribute__ ((no_instrument_function))
void __cyg_profile_func_exit(void * this_fn, void * call_site) {
    //UNUSED(call_site);

    unsigned int channel = 0;

    unsigned long data = (unsigned long)this_fn;

    int event = 0;
    int blocking = 1;
    int marked = 0;
    int flag = 0;
    int timestamp = 1;
    unsigned int mailbox = (event     << 4)
                         | (blocking  << 3)
                         | (marked    << 2)
                         | (flag      << 1)
                         | (timestamp << 0);

    unsigned long base_addr = 1024;
    unsigned long addr = SI_BASE + base_addr + channel*0x200 + mailbox*0x10;
    *(volatile unsigned long*)addr = data;
}

#ifdef __cplusplus
extern "C"
#endif
__attribute__ ((no_instrument_function))
void __cyg_profile_func_enter(void * this_fn, void * call_site) {
    //UNUSED(call_site);

    unsigned int channel = 1;

    unsigned long data = (unsigned long)this_fn;

    int event = 0;
    int blocking = 1;
    int marked = 0;
    int flag = 0;
    int timestamp = 1;
    unsigned int mailbox = (event     << 4)
                         | (blocking  << 3)
                         | (marked    << 2)
                         | (flag      << 1)
                         | (timestamp << 0);

    unsigned long base_addr = 1024;
    unsigned long addr = SI_BASE + base_addr + channel*0x200 + mailbox*0x10;
    *(volatile unsigned long*)addr = data;
}

