# HuffZip — File Compressor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-indigo.svg)](https://www.python.org/)
[![C: C11](https://img.shields.io/badge/C-C11-00599C.svg)](https://en.wikipedia.org/wiki/C11_(C_standard_revision))
[![Platform: Windows%20%7C%20Linux%20%7C%20macOS](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-slate.svg)]()

> **Simple, fast, Huffman-powered compression.**

**HuffZip** is a modern, beginner-friendly desktop application for compressing and decompressing files using **Huffman Coding**. It pairs a high-performance, modular C engine with an intuitive dark-themed GUI built using Python and CustomTkinter.

Whether you're compressing large text documents or inspecting raw binary files, HuffZip performs genuine, bit-exact lossless compression with zero simulation.

---

## Screenshots

> *Placeholder: Add real application screenshots here before publishing.*

| Compressor View | Decompressor View |
| :---: | :---: |
| ![Compressor Screenshot Placeholder](docs/screenshots/compressor_mockup.png) | ![Decompressor Screenshot Placeholder](docs/screenshots/decompressor_mockup.png) |
| *Drag-and-drop workspace with real-time compression statistics.* | *Instant `.huff` format verification and lossless restoration.* |

---

## Key Features

- **⚡ Genuine Huffman Compression:** Powered by a native C backend featuring min-heap priority queues, binary tree construction, and bit-level stream I/O.
- **🎨 Modern Dark Theme Interface:** Built with CustomTkinter featuring dark charcoal surfaces, clean typography, rounded cards, and indigo accents.
- **🖱️ Drag-and-Drop Support:** Drag files directly from Windows File Explorer into the drop zone, with a seamless file-browser fallback.
- **🔍 Two Dedicated Workspaces:** Clean segmented navigation separating the **Compressor** from the **Decompressor**.
- **📊 Real Compression Statistics:** Transparent reporting of original size, compressed size, space saved (in bytes & %), and compression ratio. Division-by-zero and header overhead are handled honestly.
- **🛡️ Overwrite Protection & Validation:** Never silently overwrites existing files. Automatically validates magic bytes (`HUFF`) and file headers before decoding.
- **📁 "Show in Folder" Action:** Reveal compressed archives or restored files in your operating system's file manager with a single click.
- **🧵 Asynchronous Execution:** Long-running compression and decompression tasks execute off the main GUI thread, keeping the window completely responsive.
- **⌨️ Keyboard Shortcuts:** Built-in productivity hotkeys (`Ctrl+O` to open, `Ctrl+Enter` to run, `Ctrl+R` to reset, `F1` for About).

---

## How Huffman Coding Works

**Huffman coding** is a classic greedy algorithm developed by David A. Huffman in 1952 for lossless data compression. 

In standard text or binary files, every character or byte is represented by a fixed length of 8 bits. Huffman coding optimizes storage by assigning **variable-length prefix codes**:
- Characters that appear **frequently** receive **short codes** (e.g., 2 to 4 bits).
- Characters that appear **rarely** receive **longer codes** (e.g., 10 to 12 bits).

```
Input Stream: "ABRACADABRA"
       ┌───────────┐
       │ Frequence │   A: 5, B: 2, R: 2, C: 1, D: 1
       └─────┬─────┘
             ▼
     [Build Min-Heap] ──► [Merge Subtrees] ──► [Huffman Tree]
                                                     ▲
                                            ┌────────┴────────┐
                                          (0)               (1)
                                         [ A ]         [ Internal ]
                                                      (0)        (1)
                                                     [ B ]      [ R ] ...
```

### The HuffZip (`.huff`) Binary Format
To decode the bitstream, the decompressor must know the exact Huffman tree. HuffZip prefixes each archive with a serialized header:
1. **Magic Bytes (4 bytes):** `HUFF`
2. **Version (1 byte):** `0x01`
3. **Original File Size (8 bytes):** Little-endian `uint64_t`
4. **Frequency Table (2,048 bytes):** 256 entries $\times$ 8-byte `uint64_t` counts
5. **Encoded Bitstream:** Variable-length bit sequences

> [!NOTE]
> Because the header requires 2,061 bytes to store the full frequency table, small files (< 2 KB) will show negative space savings. For larger text files or repetitive data, significant compression is achieved.

---

## Technologies Used

- **Backend:** C (C11 standard), GCC / MinGW, Make
- **Frontend / GUI:** Python 3.9+, CustomTkinter, TkinterDnD2, Darkdetect
- **Inter-process Communication:** Python `subprocess` with safe argument lists and background daemon threads

---

## Prerequisites & Installation

### Prerequisites
1. **Python 3.9 or newer**: [Download Python](https://www.python.org/downloads/) *(Ensure **"Add Python to PATH"** is checked on Windows).*
2. **GCC Compiler (MinGW on Windows or GCC on Linux)**:
   - **Windows:** Install [MinGW-w64](https://www.mingw-w64.org/) or [w64devkit](https://github.com/skeeto/w64devkit/releases).
   - **Ubuntu/Debian:** `sudo apt install build-essential`
   - **macOS:** `xcode-select --install`

---

## Step-by-Step Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/HuffZip.git
cd HuffZip
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Compile the C Backend
You can build the backend manually using `make` or `gcc`:

**Using Make:**
```bash
make
```

**Using GCC directly (Windows):**
```bash
gcc -std=c11 -Wall -Wextra -Wpedantic -O2 -o backend/huff.exe backend/main.c backend/huffman.c backend/heap.c backend/fileio.c backend/utils.c
```

**Using GCC directly (Linux / macOS):**
```bash
gcc -std=c11 -Wall -Wextra -Wpedantic -O2 -o backend/huff backend/main.c backend/huffman.c backend/heap.c backend/fileio.c backend/utils.c
```

*(Note: If you run `run.bat` on Windows or launch the GUI directly, HuffZip will detect GCC and compile the backend automatically if the executable is missing!)*

---

## Launching the Application

### Option A: Quick Launcher (Windows)
Double-click `run.bat` or execute in Command Prompt:
```cmd
run.bat
```

### Option B: Quick Launcher (Linux / macOS)
```bash
chmod +x run.sh
./run.sh
```

### Option C: Python Command
```bash
python main.py
```

---

## Application Usage Guide

### 🗜️ Compressor Workspace
1. **Select Input File:**
   - Drag and drop any text or binary file onto the drop zone, or click **"Choose File"**.
   - Review file metadata (name, size, extension).
2. **Configure Output:**
   - The destination defaults to the same folder with `.huff` appended.
   - Click **"Browse..."** or modify the filename if desired.
3. **Compress:**
   - Click **"Compress File"** (or press `Ctrl+Enter`).
   - Monitor the activity indicator.
   - Upon completion, review the **Compression Summary** card displaying space saved and compression ratio.
   - Click **"📁 Show in Folder"** to reveal the new archive in File Explorer.

### 📂 Decompressor Workspace
1. **Select Compressed Archive:**
   - Switch to the **Decompressor** tab.
   - Drag and drop your `.huff` file or click **"Choose Compressed File"**.
   - HuffZip instantly verifies the header magic bytes and format version.
2. **Configure Destination:**
   - The suggested filename automatically strips `.huff`.
3. **Decompress:**
   - Click **"Decompress File"** (or press `Ctrl+Enter`).
   - The file is restored byte-for-byte to its original state.
   - Click **"📁 Show in Folder"** to locate the extracted file.

---

## Command-Line Usage (C Backend)

You can also use the C backend directly in your terminal:

### Compress a file
```bash
./backend/huff.exe compress input.txt output.huff
```

### Compress with printed code table (`--verbose` / `-v`)
```bash
./backend/huff.exe compress --verbose input.bin output.huff
```

### Decompress a file
```bash
./backend/huff.exe decompress output.huff restored.txt
```

---

## Running the Automated Test Suite

A comprehensive test suite verifies round-trip lossless fidelity across text, binary, empty, and corrupted files:

```bash
python -m unittest discover -s tests -v
```

Output:
```
test_binary_file_roundtrip ... ok
test_corrupted_file_decompression ... ok
test_empty_file_handling ... ok
test_text_file_roundtrip ... ok
test_format_size ... ok
test_run_compress_identical_paths ... ok
test_run_compress_missing_input ... ok
test_validate_huff_header ... ok

Ran 8 tests in 0.14s - OK
```

---

## Project Structure

```
HuffZip/
├── backend/
│   ├── main.c           # CLI parsing and top-level execution
│   ├── huffman.c        # Huffman tree construction & code generation
│   ├── huffman.h        # Tree data structures and API
│   ├── fileio.c         # Binary header serialization & bit stream I/O
│   ├── fileio.h         # BitWriter and BitReader definitions
│   ├── heap.c           # Min-heap priority queue implementation
│   ├── heap.h           # Min-heap data structure
│   ├── utils.c          # Reporting and utility functions
│   ├── utils.h          # Error printing and size calculations
│   └── Makefile         # Backend compilation rules
├── gui/
│   ├── __init__.py      # GUI package entry
│   ├── app.py           # Main CustomTkinter application window
│   ├── components.py    # DropZone, OutputConfig, StatsCard, Dialogs
│   ├── backend_runner.py# Subprocess integration & header validation
│   └── styles.py        # Dark charcoal theme palette & fonts
├── tests/
│   ├── test_backend.py  # Lossless round-trip & binary tests
│   └── test_gui_backend_runner.py # Unit tests for runner & header checks
├── main.py              # Root launcher script
├── run.bat              # Windows one-click launcher
├── run.sh               # Linux/macOS launcher
├── Makefile             # Root Makefile delegating to backend
├── requirements.txt     # Python dependencies
├── .gitignore           # Clean repository exclusions
├── LICENSE              # MIT License
└── README.md            # Complete documentation
```

---

## Troubleshooting Common Issues

- **"Drag-and-drop driver not detected"**:
  - `tkinterdnd2` may not support all environments without Tk installed. The GUI automatically detects this and falls back gracefully to the **"Choose File"** file picker.
- **"GCC compiler not found"**:
  - Install MinGW or GCC and ensure its `bin/` directory is added to your system `PATH` environment variable.
- **"Output file is larger than input"**:
  - The Huffman header requires 2,061 bytes to store the 256-symbol frequency table. Files smaller than ~2 KB will naturally experience size overhead.
- **"Invalid magic header"**:
  - The decompressor only accepts valid archives created by HuffZip (`HUFF` signature). Files compressed with gzip, zip, or other formats cannot be extracted.

---

## License

This project is licensed under the [MIT License](LICENSE).
