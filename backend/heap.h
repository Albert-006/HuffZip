#ifndef HEAP_H
#define HEAP_H

#include <stddef.h>

struct HuffmanNode;

typedef struct MinHeap {
    size_t size;
    size_t capacity;
    struct HuffmanNode **data;
} MinHeap;

MinHeap *heap_create(size_t capacity);
void heap_destroy(MinHeap *heap);
int heap_insert(MinHeap *heap, struct HuffmanNode *node);
struct HuffmanNode *heap_extract_min(MinHeap *heap);

#endif
