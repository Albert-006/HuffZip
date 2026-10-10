#include "utils.h"

#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>

void utils_print_error(const char *message, const char *path) {
    if (path != NULL) {
        fprintf(stderr, "%s '%s': %s\n", message, path, strerror(errno));
    } else {
        fprintf(stderr, "%s: %s\n", message, strerror(errno));
    }
}

uint64_t utils_file_size(FILE *file) {
    long current;
    long end;

    current = ftell(file);
    if (current < 0) {
        return 0;
    }

    if (fseek(file, 0, SEEK_END) != 0) {
        return 0;
    }

    end = ftell(file);
    if (end < 0) {
        return 0;
    }

    if (fseek(file, current, SEEK_SET) != 0) {
        return 0;
    }

    return (uint64_t)end;
}

void utils_print_compression_report(uint64_t original_size, uint64_t compressed_size) {
    double ratio;

    if (original_size == 0) {
        printf("Original size: 0 bytes\nCompressed size: %llu bytes\nCompression ratio: N/A\n",
            (unsigned long long)compressed_size);
        return;
    }

    ratio = 100.0 * (1.0 - ((double)compressed_size / (double)original_size));
    printf("Original size: %llu bytes\nCompressed size: %llu bytes\nSpace savings: %.2f%%\n",
        (unsigned long long)original_size,
        (unsigned long long)compressed_size,
        ratio);
}

static void print_symbol(FILE *stream, unsigned int symbol) {
    if (isprint(symbol)) {
        fprintf(stream, "'%c'", symbol);
    } else {
        fprintf(stream, "0x%02X", symbol);
    }
}

void utils_print_codes(const HuffmanCode codes[256], const uint64_t freq[256], FILE *stream) {
    size_t i;
    size_t bit_index;

    fprintf(stream, "Huffman codes:\n");
    for (i = 0; i < 256; ++i) {
        if (freq[i] == 0 || codes[i].length == 0) {
            continue;
        }

        print_symbol(stream, (unsigned int)i);
        fprintf(stream, " freq=%llu code=",
            (unsigned long long)freq[i]);
        for (bit_index = 0; bit_index < codes[i].length; ++bit_index) {
            fputc(codes[i].bits[bit_index] ? '1' : '0', stream);
        }
        fputc('\n', stream);
    }
}
