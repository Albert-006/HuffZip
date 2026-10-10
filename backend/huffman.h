#ifndef HUFFMAN_H
#define HUFFMAN_H

#include <stddef.h>
#include <stdint.h>

typedef struct HuffmanNode {
    unsigned char data;
    uint64_t freq;
    struct HuffmanNode *left;
    struct HuffmanNode *right;
} HuffmanNode;

typedef struct HuffmanCode {
    unsigned char bits[256];
    size_t length;
} HuffmanCode;

HuffmanNode *huffman_build_tree(const uint64_t freq[256]);
void huffman_generate_codes(const HuffmanNode *root, HuffmanCode codes[256]);
void huffman_free_tree(HuffmanNode *root);
size_t huffman_unique_symbol_count(const uint64_t freq[256]);
int huffman_is_leaf(const HuffmanNode *node);

#endif
