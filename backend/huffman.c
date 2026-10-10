#include "huffman.h"

#include <stdlib.h>
#include <string.h>

#include "heap.h"

static HuffmanNode *node_create(unsigned char data, uint64_t freq, HuffmanNode *left, HuffmanNode *right) {
    HuffmanNode *node = (HuffmanNode *)malloc(sizeof(*node));
    if (node == NULL) {
        return NULL;
    }

    node->data = data;
    node->freq = freq;
    node->left = left;
    node->right = right;
    return node;
}

static void free_if_present(HuffmanNode *node) {
    if (node != NULL) {
        huffman_free_tree(node);
    }
}

size_t huffman_unique_symbol_count(const uint64_t freq[256]) {
    size_t count = 0;
    size_t i;

    for (i = 0; i < 256; ++i) {
        if (freq[i] > 0) {
            count++;
        }
    }

    return count;
}

int huffman_is_leaf(const HuffmanNode *node) {
    return node != NULL && node->left == NULL && node->right == NULL;
}

HuffmanNode *huffman_build_tree(const uint64_t freq[256]) {
    MinHeap *heap;
    HuffmanNode *left;
    HuffmanNode *right;
    HuffmanNode *parent;
    size_t i;
    size_t unique = huffman_unique_symbol_count(freq);

    if (unique == 0) {
        return NULL;
    }

    heap = heap_create(unique);
    if (heap == NULL) {
        return NULL;
    }

    for (i = 0; i < 256; ++i) {
        if (freq[i] == 0) {
            continue;
        }

        parent = node_create((unsigned char)i, freq[i], NULL, NULL);
        if (parent == NULL || !heap_insert(heap, parent)) {
            free_if_present(parent);
            while ((parent = heap_extract_min(heap)) != NULL) {
                huffman_free_tree(parent);
            }
            heap_destroy(heap);
            return NULL;
        }
    }

    while (heap->size > 1) {
        left = heap_extract_min(heap);
        right = heap_extract_min(heap);
        parent = node_create(left->data < right->data ? left->data : right->data,
            left->freq + right->freq, left, right);
        if (parent == NULL || !heap_insert(heap, parent)) {
            free_if_present(parent);
            huffman_free_tree(left);
            huffman_free_tree(right);
            while ((parent = heap_extract_min(heap)) != NULL) {
                huffman_free_tree(parent);
            }
            heap_destroy(heap);
            return NULL;
        }
    }

    parent = heap_extract_min(heap);
    heap_destroy(heap);
    return parent;
}

static void generate_codes_recursive(const HuffmanNode *node,
    unsigned char path[256], size_t depth, HuffmanCode codes[256]) {
    if (node == NULL) {
        return;
    }

    if (huffman_is_leaf(node)) {
        if (depth == 0) {
            path[0] = 0;
            depth = 1;
        }

        memcpy(codes[node->data].bits, path, depth);
        codes[node->data].length = depth;
        return;
    }

    path[depth] = 0;
    generate_codes_recursive(node->left, path, depth + 1, codes);

    path[depth] = 1;
    generate_codes_recursive(node->right, path, depth + 1, codes);
}

void huffman_generate_codes(const HuffmanNode *root, HuffmanCode codes[256]) {
    unsigned char path[256] = {0};
    size_t i;

    for (i = 0; i < 256; ++i) {
        codes[i].length = 0;
        memset(codes[i].bits, 0, sizeof(codes[i].bits));
    }

    generate_codes_recursive(root, path, 0, codes);
}

void huffman_free_tree(HuffmanNode *root) {
    if (root == NULL) {
        return;
    }

    huffman_free_tree(root->left);
    huffman_free_tree(root->right);
    free(root);
}
