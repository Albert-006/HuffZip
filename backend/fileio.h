#ifndef FILEIO_H
#define FILEIO_H

#include <stdint.h>
#include <stdio.h>

#include "huffman.h"

typedef struct HuffHeader {
    uint64_t original_size;
    uint64_t freq[256];
} HuffHeader;

typedef struct BitWriter {
    FILE *file;
    unsigned char buffer;
    unsigned char bits_filled;
} BitWriter;

typedef struct BitReader {
    FILE *file;
    unsigned char buffer;
    unsigned char bits_left;
} BitReader;

int fileio_compute_frequencies(const char *path, uint64_t freq[256], uint64_t *size_out);
int fileio_open_files(const char *input_path, const char *output_path, FILE **input, FILE **output, const char *output_mode);
int fileio_write_header(FILE *output, const HuffHeader *header);
int fileio_read_header(FILE *input, HuffHeader *header);
void bitwriter_init(BitWriter *writer, FILE *file);
int bitwriter_write_bit(BitWriter *writer, unsigned char bit);
int bitwriter_flush(BitWriter *writer);
void bitreader_init(BitReader *reader, FILE *file);
int bitreader_read_bit(BitReader *reader, unsigned char *bit);
int fileio_encode_stream(FILE *input, FILE *output, const HuffmanCode codes[256]);
int fileio_decode_stream(FILE *input, FILE *output, const HuffmanNode *root, uint64_t original_size);

#endif
