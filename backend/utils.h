#ifndef UTILS_H
#define UTILS_H

#include <stdint.h>
#include <stdio.h>

#include "huffman.h"

void utils_print_error(const char *message, const char *path);
void utils_print_compression_report(uint64_t original_size, uint64_t compressed_size);
uint64_t utils_file_size(FILE *file);
void utils_print_codes(const HuffmanCode codes[256], const uint64_t freq[256], FILE *stream);

#endif
