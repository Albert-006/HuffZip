@echo off
setlocal enabledelayedexpansion
title HuffZip — File Compressor

echo ====================================================
echo           HuffZip - Desktop File Compressor
echo ====================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found on your system PATH.
    echo Please install Python 3.9+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check and install Python dependencies
echo [*] Checking Python dependencies...
python -c "import customtkinter, tkinterdnd2" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [*] Installing required Python packages (customtkinter, tkinterdnd2)...
    python -m pip install -r "%~dp0requirements.txt"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

:: 3. Check C backend binary
if not exist "%~dp0backend\huff.exe" (
    echo [*] Compiled backend not found. Attempting to build backend with GCC...
    where gcc >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [WARNING] GCC compiler not found in PATH.
        echo The GUI will attempt automatic compilation or use an existing binary.
    ) else (
        echo [*] Compiling C Huffman engine...
        cd /d "%~dp0backend"
        gcc -std=c11 -Wall -Wextra -Wpedantic -O2 -o huff.exe main.c huffman.c heap.c fileio.c utils.c
        cd /d "%~dp0"
        if exist "%~dp0backend\huff.exe" (
            echo [OK] Backend built successfully!
        ) else (
            echo [ERROR] GCC failed to compile backend.
            pause
            exit /b 1
        )
    )
)

:: 4. Start the GUI Application
echo [*] Launching HuffZip GUI...
python "%~dp0main.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] HuffZip exited with an error code: %ERRORLEVEL%
    pause
)
