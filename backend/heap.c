#include "heap.h"

#include <stdlib.h>

#include "huffman.h"

static void heap_swap(struct HuffmanNode **a, struct HuffmanNode **b) {
    struct HuffmanNode *tmp = *a;
    *a = *b;
    *b = tmp;
}

static int node_less(const struct HuffmanNode *lhs, const struct HuffmanNode *rhs) {
    if (lhs->freq != rhs->freq) {
        return lhs->freq < rhs->freq;
    }
    return lhs->data < rhs->data;
}

static void heapify_up(MinHeap *heap, size_t index) {
    while (index > 0) {
        size_t parent = (index - 1U) / 2U;
        if (!node_less(heap->data[index], heap->data[parent])) {
            break;
        }
        heap_swap(&heap->data[index], &heap->data[parent]);
        index = parent;
    }
}

static void heapify_down(MinHeap *heap, size_t index) {
    while (1) {
        size_t smallest = index;
        size_t left = 2U * index + 1U;
        size_t right = 2U * index + 2U;

        if (left < heap->size && node_less(heap->data[left], heap->data[smallest])) {
            smallest = left;
        }
        if (right < heap->size && node_less(heap->data[right], heap->data[smallest])) {
            smallest = right;
        }
        if (smallest == index) {
            return;
        }

        heap_swap(&heap->data[index], &heap->data[smallest]);
        index = smallest;
    }
}

MinHeap *heap_create(size_t capacity) {
    MinHeap *heap = (MinHeap *)malloc(sizeof(*heap));
    if (heap == NULL) {
        return NULL;
    }

    heap->size = 0;
    heap->capacity = capacity > 0 ? capacity : 1;
    heap->data = (struct HuffmanNode **)calloc(heap->capacity, sizeof(*heap->data));
    if (heap->data == NULL) {
        free(heap);
        return NULL;
    }

    return heap;
}

void heap_destroy(MinHeap *heap) {
    if (heap == NULL) {
        return;
    }

    free(heap->data);
    free(heap);
}

int heap_insert(MinHeap *heap, struct HuffmanNode *node) {
    struct HuffmanNode **resized = NULL;

    if (heap == NULL || node == NULL) {
        return 0;
    }

    if (heap->size == heap->capacity) {
        size_t new_capacity = heap->capacity * 2U;
        resized = (struct HuffmanNode **)realloc(heap->data, new_capacity * sizeof(*heap->data));
        if (resized == NULL) {
            return 0;
        }
        heap->data = resized;
        heap->capacity = new_capacity;
    }

    heap->data[heap->size] = node;
    heapify_up(heap, heap->size);
    heap->size++;
    return 1;
}

struct HuffmanNode *heap_extract_min(MinHeap *heap) {
    struct HuffmanNode *min_node;

    if (heap == NULL || heap->size == 0) {
        return NULL;
    }

    min_node = heap->data[0];
    heap->size--;
    if (heap->size > 0) {
        heap->data[0] = heap->data[heap->size];
        heapify_down(heap, 0);
    }

    return min_node;
}
