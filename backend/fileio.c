#include "fileio.h"

#include <errno.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "utils.h"

static const unsigned char HUFF_MAGIC[4] = {'H', 'U', 'F', 'F'};
static const unsigned char HUFF_VERSION = 1;

static int write_u64_le(FILE *file, uint64_t value) {
    unsigned char bytes[8];
    size_t i;

    for (i = 0; i < 8; ++i) {
        bytes[i] = (unsigned char)((value >> (i * 8U)) & 0xFFU);
    }

    return fwrite(bytes, 1, sizeof(bytes), file) == sizeof(bytes);
}

static int read_u64_le(FILE *file, uint64_t *value) {
    unsigned char bytes[8];
    size_t i;
    uint64_t result = 0;

    if (fread(bytes, 1, sizeof(bytes), file) != sizeof(bytes)) {
        return 0;
    }

    for (i = 0; i < 8; ++i) {
        result |= ((uint64_t)bytes[i]) << (i * 8U);
    }

    *value = result;
    return 1;
}

int fileio_compute_frequencies(const char *path, uint64_t freq[256], uint64_t *size_out) {
    FILE *input;
    unsigned char buffer[8192];
    size_t bytes_read;
    size_t i;
    uint64_t total = 0;

    memset(freq, 0, 256 * sizeof(freq[0]));

    input = fopen(path, "rb");
    if (input == NULL) {
        return 0;
    }

    while ((bytes_read = fread(buffer, 1, sizeof(buffer), input)) > 0) {
        total += (uint64_t)bytes_read;
        for (i = 0; i < bytes_read; ++i) {
            freq[buffer[i]]++;
        }
    }

    if (ferror(input)) {
        fclose(input);
        return 0;
    }

    fclose(input);
    *size_out = total;
    return 1;
}

int fileio_open_files(const char *input_path, const char *output_path, FILE **input, FILE **output, const char *output_mode) {
    *input = fopen(input_path, "rb");
    if (*input == NULL) {
        return 0;
    }

    *output = fopen(output_path, output_mode);
    if (*output == NULL) {
        fclose(*input);
        *input = NULL;
        return 0;
    }

    return 1;
}

int fileio_write_header(FILE *output, const HuffHeader *header) {
    size_t i;

    if (fwrite(HUFF_MAGIC, 1, sizeof(HUFF_MAGIC), output) != sizeof(HUFF_MAGIC)) {
        return 0;
    }

    if (fputc(HUFF_VERSION, output) == EOF) {
        return 0;
    }

    if (!write_u64_le(output, header->original_size)) {
        return 0;
    }

    for (i = 0; i < 256; ++i) {
        if (!write_u64_le(output, header->freq[i])) {
            return 0;
        }
    }

    return 1;
}

int fileio_read_header(FILE *input, HuffHeader *header) {
    unsigned char magic[4];
    int version;
    size_t i;

    if (fread(magic, 1, sizeof(magic), input) != sizeof(magic)) {
        return 0;
    }

    if (memcmp(magic, HUFF_MAGIC, sizeof(HUFF_MAGIC)) != 0) {
        errno = EINVAL;
        return 0;
    }

    version = fgetc(input);
    if (version == EOF || (unsigned char)version != HUFF_VERSION) {
        errno = EINVAL;
        return 0;
    }

    if (!read_u64_le(input, &header->original_size)) {
        return 0;
    }

    for (i = 0; i < 256; ++i) {
        if (!read_u64_le(input, &header->freq[i])) {
            return 0;
        }
    }

    return 1;
}

void bitwriter_init(BitWriter *writer, FILE *file) {
    writer->file = file;
    writer->buffer = 0;
    writer->bits_filled = 0;
}

int bitwriter_write_bit(BitWriter *writer, unsigned char bit) {
    writer->buffer = (unsigned char)((writer->buffer << 1U) | (bit & 1U));
    writer->bits_filled++;

    if (writer->bits_filled == 8U) {
        if (fputc(writer->buffer, writer->file) == EOF) {
            return 0;
        }
        writer->buffer = 0;
        writer->bits_filled = 0;
    }

    return 1;
}

int bitwriter_flush(BitWriter *writer) {
    if (writer->bits_filled == 0U) {
        return 1;
    }

    writer->buffer <<= (unsigned char)(8U - writer->bits_filled);
    if (fputc(writer->buffer, writer->file) == EOF) {
        return 0;
    }

    writer->buffer = 0;
    writer->bits_filled = 0;
    return 1;
}

void bitreader_init(BitReader *reader, FILE *file) {
    reader->file = file;
    reader->buffer = 0;
    reader->bits_left = 0;
}

int bitreader_read_bit(BitReader *reader, unsigned char *bit) {
    int ch;

    if (reader->bits_left == 0U) {
        ch = fgetc(reader->file);
        if (ch == EOF) {
            return 0;
        }
        reader->buffer = (unsigned char)ch;
        reader->bits_left = 8U;
    }

    *bit = (unsigned char)((reader->buffer >> 7U) & 1U);
    reader->buffer <<= 1U;
    reader->bits_left--;
    return 1;
}

int fileio_encode_stream(FILE *input, FILE *output, const HuffmanCode codes[256]) {
    BitWriter writer;
    unsigned char buffer[8192];
    size_t bytes_read;
    size_t i;
    size_t bit_index;

    bitwriter_init(&writer, output);

    while ((bytes_read = fread(buffer, 1, sizeof(buffer), input)) > 0) {
        for (i = 0; i < bytes_read; ++i) {
            const HuffmanCode *code = &codes[buffer[i]];
            for (bit_index = 0; bit_index < code->length; ++bit_index) {
                if (!bitwriter_write_bit(&writer, code->bits[bit_index])) {
                    return 0;
                }
            }
        }
    }

    if (ferror(input)) {
        return 0;
    }

    return bitwriter_flush(&writer);
}

int fileio_decode_stream(FILE *input, FILE *output, const HuffmanNode *root, uint64_t original_size) {
    BitReader reader;
    const HuffmanNode *current;
    unsigned char bit;
    uint64_t written = 0;

    if (original_size == 0) {
        return 1;
    }

    if (root == NULL) {
        errno = EINVAL;
        return 0;
    }

    if (huffman_is_leaf(root)) {
        while (written < original_size) {
            if (fputc(root->data, output) == EOF) {
                return 0;
            }
            written++;
        }
        return 1;
    }

    bitreader_init(&reader, input);
    current = root;

    while (written < original_size) {
        if (!bitreader_read_bit(&reader, &bit)) {
            errno = EINVAL;
            return 0;
        }

        current = bit == 0 ? current->left : current->right;
        if (current == NULL) {
            errno = EINVAL;
            return 0;
        }

        if (huffman_is_leaf(current)) {
            if (fputc(current->data, output) == EOF) {
                return 0;
            }
            written++;
            current = root;
        }
    }

    return 1;
}
