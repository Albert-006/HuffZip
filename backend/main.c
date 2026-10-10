#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "fileio.h"
#include "huffman.h"
#include "utils.h"

typedef struct CliOptions {
    const char *mode;
    const char *input_path;
    const char *output_path;
    int verbose;
} CliOptions;

static void print_usage(const char *program_name) {
    fprintf(stderr,
        "Usage:\n"
        "  %s compress [-v|--verbose] <input> <output>\n"
        "  %s decompress <input.huff> <output>\n",
        program_name, program_name);
}

static int parse_args(int argc, char *argv[], CliOptions *options) {
    memset(options, 0, sizeof(*options));

    if (argc < 4) {
        return 0;
    }

    options->mode = argv[1];

    if (strcmp(options->mode, "compress") == 0) {
        int arg_index = 2;
        if (argc == 5 && (strcmp(argv[2], "-v") == 0 || strcmp(argv[2], "--verbose") == 0)) {
            options->verbose = 1;
            arg_index = 3;
        } else if (argc != 4) {
            return 0;
        }

        options->input_path = argv[arg_index];
        options->output_path = argv[arg_index + 1];
        return 1;
    }

    if (strcmp(options->mode, "decompress") == 0 && argc == 4) {
        options->input_path = argv[2];
        options->output_path = argv[3];
        return 1;
    }

    return 0;
}

static int compress_file(const CliOptions *options) {
    HuffHeader header;
    HuffmanNode *root = NULL;
    HuffmanCode codes[256];
    FILE *input = NULL;
    FILE *output = NULL;
    uint64_t compressed_size;

    if (!fileio_compute_frequencies(options->input_path, header.freq, &header.original_size)) {
        utils_print_error("Failed to read input file", options->input_path);
        return 1;
    }

    root = huffman_build_tree(header.freq);
    huffman_generate_codes(root, codes);

    if (!fileio_open_files(options->input_path, options->output_path, &input, &output, "wb")) {
        utils_print_error("Failed to open file", errno == 0 ? NULL : (input == NULL ? options->input_path : options->output_path));
        huffman_free_tree(root);
        return 1;
    }

    if (!fileio_write_header(output, &header)) {
        utils_print_error("Failed to write output file", options->output_path);
        fclose(input);
        fclose(output);
        huffman_free_tree(root);
        return 1;
    }

    if (header.original_size > 0 && !fileio_encode_stream(input, output, codes)) {
        utils_print_error("Failed to encode file", options->output_path);
        fclose(input);
        fclose(output);
        huffman_free_tree(root);
        return 1;
    }

    if (fflush(output) != 0) {
        utils_print_error("Failed to flush output file", options->output_path);
        fclose(input);
        fclose(output);
        huffman_free_tree(root);
        return 1;
    }

    compressed_size = utils_file_size(output);
    fclose(input);
    fclose(output);

    if (options->verbose) {
        utils_print_codes(codes, header.freq, stdout);
    }
    utils_print_compression_report(header.original_size, compressed_size);

    huffman_free_tree(root);
    return 0;
}

static int decompress_file(const CliOptions *options) {
    HuffHeader header;
    HuffmanNode *root = NULL;
    FILE *input = NULL;
    FILE *output = NULL;

    if (!fileio_open_files(options->input_path, options->output_path, &input, &output, "wb")) {
        utils_print_error("Failed to open file", errno == 0 ? NULL : (input == NULL ? options->input_path : options->output_path));
        return 1;
    }

    if (!fileio_read_header(input, &header)) {
        utils_print_error("Failed to read compressed file", options->input_path);
        fclose(input);
        fclose(output);
        return 1;
    }

    root = huffman_build_tree(header.freq);
    if (!fileio_decode_stream(input, output, root, header.original_size)) {
        utils_print_error("Failed to decode file", options->input_path);
        fclose(input);
        fclose(output);
        huffman_free_tree(root);
        return 1;
    }

    fclose(input);
    fclose(output);
    huffman_free_tree(root);
    return 0;
}

int main(int argc, char *argv[]) {
    CliOptions options;

    if (!parse_args(argc, argv, &options)) {
        print_usage(argv[0]);
        return EXIT_FAILURE;
    }

    if (strcmp(options.mode, "compress") == 0) {
        return compress_file(&options);
    }

    if (strcmp(options.mode, "decompress") == 0) {
        return decompress_file(&options);
    }

    print_usage(argv[0]);
    return EXIT_FAILURE;
}
