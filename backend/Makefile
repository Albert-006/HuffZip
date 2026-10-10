CC ?= gcc
CFLAGS ?= -std=c11 -Wall -Wextra -Wpedantic -O2
TARGET = huff

SOURCES = main.c huffman.c heap.c fileio.c utils.c
OBJECTS = $(SOURCES:.c=.o)

ifeq ($(OS),Windows_NT)
    TARGET_BIN = $(TARGET).exe
else
    TARGET_BIN = $(TARGET)
endif

all: $(TARGET_BIN)

$(TARGET_BIN): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $(OBJECTS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
ifeq ($(OS),Windows_NT)
	-del /Q $(OBJECTS) $(TARGET_BIN) 2>NUL
else
	rm -f $(OBJECTS) $(TARGET_BIN)
endif

.PHONY: all clean
