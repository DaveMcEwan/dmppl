.globl _boot
.globl _get_heap_start
.globl _flush_dcache
.globl _delay_cycles

.globl _start
.globl _end

.section .init, "ax"

.set _stack_start, _end
#.set _stack_size, 65536 # 64KiB stack
.set _stack_size, 16777216 # 16MiB stack
.set _stack_end, _stack_start + _stack_size
.set _heap_start, _stack_end


_boot:
    # Initialise all registers to something unlikely, for debug
    lui x1, 0xf0000
    #lui x2, 0xf0000
    #lui x3, 0xf0000
    lui x4, 0xf0000
    lui x5, 0xf0000
    lui x6, 0xf0000
    lui x7, 0xf0000
    lui x8, 0xf0000
    lui x9, 0xf0000
    lui x10, 0xf0000
    lui x11, 0xf0000
    lui x12, 0xf0000
    lui x13, 0xf0000
    lui x14, 0xf0000
    lui x15, 0xf0000
    lui x16, 0xf0000
    lui x17, 0xf0000
    lui x18, 0xf0000
    lui x19, 0xf0000
    lui x20, 0xf0000
    lui x21, 0xf0000
    lui x22, 0xf0000
    lui x23, 0xf0000
    lui x24, 0xf0000
    lui x25, 0xf0000
    lui x26, 0xf0000
    lui x27, 0xf0000
    lui x28, 0xf0000
    lui x29, 0xf0000
    lui x30, 0xf0000
    lui x31, 0xf0000

    # Enable FPU and extensions.
    # If not present then this will be ignored.
    li x2, (1 << 13) | (1 << 15)
    csrs mstatus, x2

    # Initialise stack pointer, beyond the _end defined by the linker
.option push
.option norelax
    lla gp, __global_pointer$
.option pop
    la sp, _stack_end

    # _start wants main parameters on stack
#if __riscv_xlen == 32
    addi sp, sp, -8
    sw zero, 0(sp)
    sw zero, 4(sp)
#else
    addi sp, sp, -16
    sd zero, 0(sp)
    sd zero, 8(sp)
#endif

    j _start
    #ebreak

.size _boot, .-_boot
.type _boot, @function


_get_heap_start:
    la a0, _heap_start
    ret

.size _get_heap_start, .-_get_heap_start
.type _get_heap_start, @function


_flush_dcache:

    fence    # this ensures all preceding strores have been done (probably redundant on Rocket)
    fence.i  # this flushes the dcache on Rocket (Rocket core modified by Marcin to allow that)
    ret

.size _flush_dcache, .-_flush_dcache
.type _flush_dcache, @function


_delay_cycles:

    srli a0, a0, 1
    beqz a0, .Ldlyend

.Ldly:
    addi a0, a0, -1
    bnez a0, .Ldly

.Ldlyend:
    ret

.size _delay_cycles, .-_delay_cycles
.type _delay_cycles, @function


