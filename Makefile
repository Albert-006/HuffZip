CC ?= gcc
CFLAGS ?= -std=c11 -Wall -Wextra -Wpedantic -O2

ifeq ($(OS),Windows_NT)
    TARGET_BIN = backend/huff.exe
else
    TARGET_BIN = backend/huff
endif

all: $(TARGET_BIN)

$(TARGET_BIN):
	$(MAKE) -C backend

clean:
	$(MAKE) -C backend clean

.PHONY: all clean
