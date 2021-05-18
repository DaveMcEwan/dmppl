
# Build all binaries with something like:
#	$ cd <Directory containing this Makefile>
#	$ make clean all
# Or like:
#	$ make clean tinn HUMAN_VISUAL_DELAY=1 UST_SI=1
#
# Parameter Descriptions
# ----------------------
# - HUMAN_VISUAL_DELAY
#	  C should have ifdefs in place to insert delays which just make things
#     slow enough for humans to watch.
# - UST_SI
#     Statically instrument all non-library functions using the UltraSoC
#	  Static Instrumentation module.
# - EXTRA_PRINTF
#     Reduce the number of printf calls.
# - SCPU_SOFT_FLOAT
#     Compile without using floating point instructions.

SOURCE := ../src
BUILD := ../temp
INSTALL_PATH := ../bin

default: all
all: helloworld
all: taygete
all: blocks
all: tinn
all: fusa_sw

# Print message onto STDOUT and STDERR from both cores.
helloworld: $(BUILD)/helloworld.acpu.bin
helloworld: $(BUILD)/helloworld.scpu.bin

# Send and receive some messages over the UltraSoC infrastructure.
taygete: $(BUILD)/taygete.acpu.bin
taygete: $(BUILD)/taygete.scpu.bin

# Draw random blocks on the LCD.
blocks: $(BUILD)/blocks.acpu.bin
blocks: $(BUILD)/blocks.scpu.bin

# Tiny Neural Network for classifying handwritten digits.
# https://github.com/glouw/tinn
tinn: $(BUILD)/tinn.acpu.bin
tinn: $(BUILD)/tinn.scpu.bin

# Demo for ResilTech.
# NOTE: Requires external demo_riscv.h
#fusa_io: $(BUILD)/fusa_io.acpu.bin
#fusa_io: $(BUILD)/fusa_io.scpu.bin

# Functional Safety Software Sequence demo (as defined by Resiltech).
fusa_sw: $(BUILD)/fusa_sw.acpu.bin
fusa_sw: $(BUILD)/fusa_sw.scpu.bin


# Symlink foo.c to foo.acpu.c and foo.scpu.c when there's only one top file for
# an app.
# Nothing is done when the app is already split into the 2 files.
$(SOURCE)/%.acpu.c: $(SOURCE)/%.c
	-ln -s $< $@
$(SOURCE)/%.scpu.c: $(SOURCE)/%.c
	-ln -s $< $@


RISCV_BIN := $(RISCV)/bin/riscv64-unknown-elf-
# The enviroment variable RISCV should point to riscv-tools:
# https://github.com/riscv/riscv-tools
#	OR if you've built the toolchain separately (a la picorv32)
#RISCV_BIN := /space/riscv32imc/bin/riscv32-unknown-elf-

# Link with libraries in $(RISCV)/riscv64-unknown-elf/lib/$(MARCH)/$(MABI)
MARCH_ACPU = rv64im
MABI_ACPU = lp64
# Avoid hard-float with something like: make dave SCPU_SOFT_FLOAT=1
ifdef SCPU_SOFT_FLOAT
MARCH_SCPU = rv64im
MABI_SCPU = lp64
else
MARCH_SCPU = rv64imafd
MABI_SCPU = lp64d
endif


# UltraSoC library objects
UST_EXT_C += taygete_msg_codec_data
UST_EXT_C += ust_msg
UST_EXT_C += ust_msg_codec_tables
UST_LIB_C += buscomm
UST_LIB_C += si
UST_LIB_C += taygete_msg
UST_LIB_C += sys_wrappers
#UST_LIB_C += taygete_fusa_sw
UST_LIB_C += fpga
UST_LIB_C += vc

UST_EXT_ACPU_O = $(patsubst %, $(BUILD)/%.ext.acpu.o, $(UST_EXT_C))
UST_EXT_SCPU_O = $(patsubst %, $(BUILD)/%.ext.scpu.o, $(UST_EXT_C))
UST_LIB_ACPU_O = $(patsubst %, $(BUILD)/%.lib.acpu.o, $(UST_LIB_C))
UST_LIB_SCPU_O = $(patsubst %, $(BUILD)/%.lib.scpu.o, $(UST_LIB_C))

UST_G++_FLAGS  = -g # Default debug information (-g0, -g1, -g, -g3)
UST_G++_FLAGS += -O2 # Optimization level (-O0, -O1/-O, -O2, -O3, -Os, -Ofast)
UST_G++_FLAGS += -fdata-sections
UST_G++_FLAGS += -ffunction-sections
UST_G++_FLAGS += -I$(SOURCE)
UST_G++_FLAGS += -I$(SOURCE)/ext
UST_G++_FLAGS += -I$(SOURCE)/lib
UST_G++_FLAGS += -DUST_ANALYTICS_BARE_METAL

# Add in delays to make things visible to slow humans.
# On tinn this adds ~0.5s to each prediction.
ifdef HUMAN_VISUAL_DELAY
UST_G++_FLAGS += -DHUMAN_VISUAL_DELAY
endif

UST_G++_WARNS  = -Werror
UST_G++_WARNS += -Wall
UST_G++_WARNS += -Wextra
UST_G++_WARNS += -Wundef
UST_G++_WARNS += -Wpointer-arith
UST_G++_WARNS += -Wwrite-strings
#UST_G++_WARNS += -Wredundant-decls
UST_G++_WARNS += -Wno-unused-parameter
UST_G++_WARNS += -Wno-unused-function

$(BUILD)/%.ext.acpu.o: $(SOURCE)/ext/%.c
	mkdir -p $(shell dirname $@)
	$(RISCV_BIN)g++ -c $(UST_G++_FLAGS) $(UST_G++_WARNS) \
		-DUST_PROTO_ACPU \
		-march=$(MARCH_ACPU) -mabi=$(MABI_ACPU) -mcmodel=medany \
		-o $@ $<
$(BUILD)/%.lib.acpu.o: $(SOURCE)/lib/%.c
	mkdir -p $(shell dirname $@)
	$(RISCV_BIN)g++ -c $(UST_G++_FLAGS) $(UST_G++_WARNS) \
		-DUST_PROTO_ACPU \
		-march=$(MARCH_ACPU) -mabi=$(MABI_ACPU) -mcmodel=medany \
		-o $@ $<
	$(RISCV_BIN)objdump -D $@ > $@.dasm

$(BUILD)/%.ext.scpu.o: $(SOURCE)/ext/%.c
	mkdir -p $(shell dirname $@)
	$(RISCV_BIN)g++ -c $(UST_G++_FLAGS) $(UST_G++_WARNS) \
		-DUST_PROTO_SCPU \
		-march=$(MARCH_SCPU) -mabi=$(MABI_SCPU) -mcmodel=medany \
		-o $@ $<
$(BUILD)/%.lib.scpu.o: $(SOURCE)/lib/%.c
	mkdir -p $(shell dirname $@)
	$(RISCV_BIN)g++ -c $(UST_G++_FLAGS) $(UST_G++_WARNS) \
		-DUST_PROTO_SCPU \
		-march=$(MARCH_SCPU) -mabi=$(MABI_SCPU) -mcmodel=medany \
		-o $@ $<
	$(RISCV_BIN)objdump -D $@ > $@.dasm

TAYGETE_BOOTSTRAP = $(PWD)/boot.S


# Final objects and linking.
LINKER_FLAGS  = -Wl,--gc-sections
LINKER_FLAGS += -Wl,-entry=_boot
LINKER_FLAGS += -Wl,--wrap=_read
LINKER_FLAGS += -Wl,--wrap=_write
LINKER_FLAGS += -Wl,--wrap=_fstat
LINKER_FLAGS += -Wl,--wrap=_lseek
LINKER_FLAGS += -Wl,--wrap=_close
LINKER_FLAGS += -Wl,--wrap=_sbrk
LINKER_FLAGS += -Wl,--wrap=exit
LINKER_FLAGS += -Wl,--wrap=_exit

# Flags for application files.
ACPU_G++_FLAGS = -DUST_PROTO_ACPU
SCPU_G++_FLAGS = -DUST_PROTO_SCPU
ifdef EXTRA_PRINTF
ACPU_G++_FLAGS += -DEXTRA_PRINTF
SCPU_G++_FLAGS += -DEXTRA_PRINTF
endif
ifdef UST_SI
ACPU_G++_FLAGS += -DUST_SI -finstrument-functions -g
SCPU_G++_FLAGS += -DUST_SI -finstrument-functions -g
endif

# Compile top level ACPU file.
$(BUILD)/%.acpu.o: $(SOURCE)/%.acpu.c
	mkdir -p $(shell dirname $@)
	$(RISCV_BIN)g++ -c $(UST_G++_WARNS) $(UST_G++_FLAGS) \
		$(ACPU_G++_FLAGS) \
		-march=$(MARCH_ACPU) -mabi=$(MABI_ACPU) -mcmodel=medany \
		-o $@ $<

# Compile top level SCPU file.
$(BUILD)/%.scpu.o: $(SOURCE)/%.scpu.c
	mkdir -p $(shell dirname $@)
	$(RISCV_BIN)g++ -c $(UST_G++_WARNS) $(UST_G++_FLAGS) \
		$(SCPU_G++_FLAGS) \
		-march=$(MARCH_SCPU) -mabi=$(MABI_SCPU) -mcmodel=medany \
		-o $@ $<

# Link ACPU objects.
$(BUILD)/%.acpu.x: $(BUILD)/%.acpu.o $(UST_EXT_ACPU_O) $(UST_LIB_ACPU_O)
	mkdir -p $(shell dirname $@)
	$(RISCV_BIN)g++ $(UST_G++_WARNS) $(UST_G++_FLAGS) \
		-march=$(MARCH_ACPU) -mabi=$(MABI_ACPU) -mcmodel=medany \
		$(LINKER_FLAGS) -Wl,-Ttext-segment=0x60000000 \
		-static -ffreestanding \
		-o $@ \
		$^ $(TAYGETE_BOOTSTRAP) -lm
	$(RISCV_BIN)objdump -D $@ > $@.dasm
	$(RISCV_BIN)objdump -d $@ > $@.dis
	$(RISCV_BIN)objdump -x $@ > $@.sym

# Link SCPU objects.
$(BUILD)/%.scpu.x: $(BUILD)/%.scpu.o $(UST_EXT_SCPU_O) $(UST_LIB_SCPU_O)
	mkdir -p $(shell dirname $@)
	$(RISCV_BIN)g++ $(UST_G++_WARNS) $(UST_G++_FLAGS) \
		-march=$(MARCH_SCPU) -mabi=$(MABI_SCPU) -mcmodel=medany \
		$(LINKER_FLAGS) -Wl,-Ttext-segment=0x70000000 \
		-static -ffreestanding \
		-o $@ \
		$^ $(TAYGETE_BOOTSTRAP) -lm
	$(RISCV_BIN)objdump -D $@ > $@.dasm
	$(RISCV_BIN)objdump -d $@ > $@.dis
	$(RISCV_BIN)objdump -x $@ > $@.sym

# Convert ELFs (*.x) to binaries and copy to where the Taygete Python system
# finds them.
$(BUILD)/%.bin: $(BUILD)/%.x
	$(RISCV_BIN)objcopy -O binary $< $@
	cp $@ $(INSTALL_PATH)/
	#scp $@ snowy:.


# Don't remove files with implicit make rules.
# Without this make assumes build/*.x are intermediate file and removes them.
.SECONDARY:

clean:
	rm -rf $(BUILD)
	find $(SOURCE) -type l -delete

