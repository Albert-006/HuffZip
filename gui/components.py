"""
UI Components for HuffZip.
Includes interactive Drag-and-Drop zone, file cards, output configuration,
statistics summary cards, status bar, and educational About dialog.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from gui.backend_runner import format_size, open_in_file_manager, validate_huff_header
from gui.styles import (
    ACCENT_AMBER,
    ACCENT_CYAN,
    ACCENT_GREEN,
    ACCENT_HOVER,
    ACCENT_PRIMARY,
    ACCENT_RED,
    BG_INPUT,
    BG_ROOT,
    BG_SURFACE,
    BG_SURFACE_HOVER,
    BORDER_ACTIVE,
    BORDER_DASHED,
    BORDER_DEFAULT,
    CORNER_RADIUS_LG,
    CORNER_RADIUS_MD,
    CORNER_RADIUS_SM,
    FONT_BADGE,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_HEADING,
    FONT_MONO,
    FONT_MONO_BOLD,
    FONT_SUBHEADING,
    FONT_SUBTITLE,
    FONT_TITLE,
    TEXT_ACCENT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

# Optional TkinterDnD2 import for Drag and Drop
try:
    from tkinterdnd2 import DND_FILES
    HAS_DND = True
except Exception:
    DND_FILES = None
    HAS_DND = False


class DropZone(ctk.CTkFrame):
    """
    Drag and Drop zone with visual hover feedback, file browser fallback,
    and selected file summary card.
    """

    def __init__(
        self,
        master,
        title: str,
        subtitle: str,
        button_text: str,
        on_file_selected: Callable[[str], None],
        on_file_cleared: Callable[[], None],
        allowed_extensions: Optional[list[str]] = None,
        is_decompressor: bool = False,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=BG_SURFACE,
            border_color=BORDER_DASHED,
            border_width=2,
            corner_radius=CORNER_RADIUS_LG,
            **kwargs,
        )

        self.title_text = title
        self.subtitle_text = subtitle
        self.button_text = button_text
        self.on_file_selected = on_file_selected
        self.on_file_cleared = on_file_cleared
        self.allowed_extensions = allowed_extensions or []
        self.is_decompressor = is_decompressor

        self.current_file: Optional[Path] = None
        self._is_hovered = False

        self._build_empty_ui()
        self._setup_dnd()

    def _build_empty_ui(self):
        """Constructs the empty drop zone UI."""
        for widget in self.winfo_children():
            widget.destroy()

        self.configure(fg_color=BG_SURFACE, border_color=BORDER_DASHED)

        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True, padx=24, pady=28)

        # Big Visual Icon
        icon_symbol = "📂" if self.is_decompressor else "🗜️"
        self.icon_label = ctk.CTkLabel(
            self.content_container,
            text=icon_symbol,
            font=("Segoe UI Emoji", 44),
        )
        self.icon_label.pack(pady=(0, 8))

        # Title / instructions
        self.title_label = ctk.CTkLabel(
            self.content_container,
            text=self.title_text,
            font=FONT_HEADING,
            text_color=TEXT_PRIMARY,
        )
        self.title_label.pack(pady=(0, 2))

        self.sub_label = ctk.CTkLabel(
            self.content_container,
            text=self.subtitle_text,
            font=FONT_CAPTION,
            text_color=TEXT_MUTED,
        )
        self.sub_label.pack(pady=(0, 16))

        # Choose File button
        self.browse_btn = ctk.CTkButton(
            self.content_container,
            text=self.button_text,
            font=FONT_BODY_BOLD,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            corner_radius=CORNER_RADIUS_MD,
            height=38,
            command=self._on_browse_click,
        )
        self.browse_btn.pack(pady=(0, 4))

        if not HAS_DND:
            self.dnd_note = ctk.CTkLabel(
                self.content_container,
                text="(Drag-and-drop driver not detected; use browse button above)",
                font=FONT_CAPTION,
                text_color=TEXT_MUTED,
            )
            self.dnd_note.pack(pady=(6, 0))

        self._setup_dnd()

    def _build_selected_ui(self, file_path: Path):
        """Constructs the card view when a file is actively selected."""
        for widget in self.winfo_children():
            widget.destroy()

        self.configure(fg_color=BG_SURFACE, border_color=BORDER_ACTIVE)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=18)

        top_row = ctk.CTkFrame(container, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 8))

        # File icon and Title
        icon_symbol = "📦" if self.is_decompressor else "📄"
        icon_lbl = ctk.CTkLabel(top_row, text=icon_symbol, font=("Segoe UI Emoji", 26))
        icon_lbl.pack(side="left", padx=(0, 12))

        info_box = ctk.CTkFrame(top_row, fg_color="transparent")
        info_box.pack(side="left", fill="x", expand=True)

        filename_lbl = ctk.CTkLabel(
            info_box,
            text=file_path.name,
            font=FONT_HEADING,
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        filename_lbl.pack(fill="x")

        # Badges (Extension & Size)
        badges_frame = ctk.CTkFrame(info_box, fg_color="transparent")
        badges_frame.pack(fill="x", pady=(3, 0))

        ext = file_path.suffix.upper() or ".FILE"
        ext_badge = ctk.CTkLabel(
            badges_frame,
            text=f" {ext} ",
            font=FONT_BADGE,
            text_color=TEXT_ACCENT,
            fg_color=BG_INPUT,
            corner_radius=CORNER_RADIUS_SM,
        )
        ext_badge.pack(side="left", padx=(0, 8))

        file_size = file_path.stat().st_size if file_path.is_file() else 0
        size_str = format_size(file_size, detailed=True)
        size_lbl = ctk.CTkLabel(
            badges_frame,
            text=f"Size: {size_str}",
            font=FONT_CAPTION,
            text_color=TEXT_SECONDARY,
        )
        size_lbl.pack(side="left")

        # Clear / Remove button
        clear_btn = ctk.CTkButton(
            top_row,
            text="✕ Remove",
            width=80,
            height=30,
            font=FONT_CAPTION,
            fg_color=BG_INPUT,
            hover_color=ACCENT_RED,
            text_color=TEXT_SECONDARY,
            corner_radius=CORNER_RADIUS_SM,
            command=self.clear_selection,
        )
        clear_btn.pack(side="right", padx=(10, 0))

        # Bottom row: Path display and Change button
        bottom_row = ctk.CTkFrame(container, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(8, 0))

        path_lbl = ctk.CTkLabel(
            bottom_row,
            text=f"Location: {str(file_path.parent)}",
            font=FONT_CAPTION,
            text_color=TEXT_MUTED,
            anchor="w",
        )
        path_lbl.pack(side="left", fill="x", expand=True)

        change_btn = ctk.CTkButton(
            bottom_row,
            text="Change File",
            width=90,
            height=28,
            font=FONT_CAPTION,
            fg_color=BG_SURFACE_HOVER,
            hover_color=ACCENT_HOVER,
            corner_radius=CORNER_RADIUS_SM,
            command=self._on_browse_click,
        )
        change_btn.pack(side="right")

        # If decompressor, show header validation badge immediately
        if self.is_decompressor:
            val_frame = ctk.CTkFrame(container, fg_color="transparent")
            val_frame.pack(fill="x", pady=(10, 0))

            is_valid, orig_size, val_err = validate_huff_header(file_path)
            if is_valid:
                orig_str = format_size(orig_size) if orig_size is not None else "Unknown"
                status_badge = ctk.CTkLabel(
                    val_frame,
                    text=f"✓ Verified HuffZip Archive (Format v1.0) • Uncompressed size: {orig_str}",
                    font=FONT_CAPTION,
                    text_color=ACCENT_GREEN,
                    anchor="w",
                )
                status_badge.pack(side="left")
            else:
                err_badge = ctk.CTkLabel(
                    val_frame,
                    text=f"⚠️ {val_err}",
                    font=FONT_CAPTION,
                    text_color=ACCENT_RED,
                    anchor="w",
                )
                err_badge.pack(side="left")

        self._setup_dnd()

    def _setup_dnd(self):
        """Recursively registers drag-and-drop handlers if TkinterDnD is available."""
        if not HAS_DND or DND_FILES is None:
            return

        def register_widget(widget):
            try:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>", self._on_drop_event)
                widget.dnd_bind("<<DropEnter>>", self._on_drag_enter)
                widget.dnd_bind("<<DropLeave>>", self._on_drag_leave)
            except Exception:
                pass
            for child in widget.winfo_children():
                register_widget(child)

        register_widget(self)

    def _on_drag_enter(self, _event=None):
        if not self.current_file:
            self.configure(fg_color=BG_SURFACE_HOVER, border_color=BORDER_ACTIVE)

    def _on_drag_leave(self, _event=None):
        if not self.current_file:
            self.configure(fg_color=BG_SURFACE, border_color=BORDER_DASHED)

    def _on_drop_event(self, event):
        self._on_drag_leave()
        data = getattr(event, "data", "")
        if not data:
            return

        # Split paths properly using tcl splitlist
        try:
            paths = list(self.winfo_toplevel().tk.splitlist(data))
        except Exception:
            paths = [data.strip("{}")]

        if not paths:
            return

        target_str = paths[0]
        target_path = Path(target_str).resolve()

        if target_path.is_dir():
            from tkinter import messagebox
            messagebox.showwarning(
                "Folder Selected",
                f"'{target_path.name}' is a directory.\n\nHuffZip operates on individual files. Please select a single file to compress or decompress.",
            )
            return

        if not target_path.is_file():
            from tkinter import messagebox
            messagebox.showerror("Invalid File", f"The dropped file could not be read:\n{target_str}")
            return

        self.set_file(target_path)

    def _on_browse_click(self):
        from tkinter import filedialog

        filetypes = []
        if self.is_decompressor:
            filetypes = [("Huffman Compressed Files", "*.huff"), ("All Files", "*.*")]
        else:
            filetypes = [("All Files", "*.*")]

        selected = filedialog.askopenfilename(
            title="Select File",
            filetypes=filetypes,
            parent=self.winfo_toplevel(),
        )
        if selected:
            self.set_file(Path(selected))

    def set_file(self, path: Path):
        """Sets the selected file and triggers callback."""
        self.current_file = path.resolve()
        self._build_selected_ui(self.current_file)
        self.on_file_selected(str(self.current_file))

    def clear_selection(self, notify: bool = True):
        """Clears selection and resets to empty state."""
        if self.current_file is None:
            return
        self.current_file = None
        self._build_empty_ui()
        if notify and self.on_file_cleared:
            self.on_file_cleared()


class OutputConfigCard(ctk.CTkFrame):
    """
    Card allowing users to configure destination folder and output filename,
    with automatic conflict/overwrite detection.
    """

    def __init__(
        self,
        master,
        default_folder: str = "",
        default_filename: str = "",
        on_change: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=BG_SURFACE,
            border_color=BORDER_DEFAULT,
            border_width=1,
            corner_radius=CORNER_RADIUS_LG,
            **kwargs,
        )

        self.on_change = on_change
        self.destination_dir = default_folder or str(Path.home())

        self._build_ui(default_filename)

    def _build_ui(self, default_filename: str):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        header_lbl = ctk.CTkLabel(
            container,
            text="Output Destination",
            font=FONT_HEADING,
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        header_lbl.pack(fill="x", pady=(0, 10))

        # Folder selection row
        folder_row = ctk.CTkFrame(container, fg_color="transparent")
        folder_row.pack(fill="x", pady=(0, 8))

        folder_lbl = ctk.CTkLabel(
            folder_row,
            text="Destination Folder:",
            font=FONT_CAPTION,
            text_color=TEXT_SECONDARY,
            width=120,
            anchor="w",
        )
        folder_lbl.pack(side="left")

        self.folder_entry = ctk.CTkEntry(
            folder_row,
            font=FONT_BODY,
            fg_color=BG_INPUT,
            border_color=BORDER_DEFAULT,
            corner_radius=CORNER_RADIUS_SM,
        )
        self.folder_entry.insert(0, self.destination_dir)
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.folder_entry.bind("<KeyRelease>", lambda _: self._on_field_change())

        browse_folder_btn = ctk.CTkButton(
            folder_row,
            text="Browse...",
            width=80,
            height=32,
            font=FONT_CAPTION,
            fg_color=BG_SURFACE_HOVER,
            hover_color=ACCENT_HOVER,
            corner_radius=CORNER_RADIUS_SM,
            command=self._on_browse_folder,
        )
        browse_folder_btn.pack(side="right")

        # Filename selection row
        file_row = ctk.CTkFrame(container, fg_color="transparent")
        file_row.pack(fill="x", pady=(0, 6))

        file_lbl = ctk.CTkLabel(
            file_row,
            text="Output Filename:",
            font=FONT_CAPTION,
            text_color=TEXT_SECONDARY,
            width=120,
            anchor="w",
        )
        file_lbl.pack(side="left")

        self.filename_entry = ctk.CTkEntry(
            file_row,
            font=FONT_BODY,
            fg_color=BG_INPUT,
            border_color=BORDER_DEFAULT,
            corner_radius=CORNER_RADIUS_SM,
        )
        self.filename_entry.insert(0, default_filename)
        self.filename_entry.pack(side="left", fill="x", expand=True, padx=(4, 8))
        self.filename_entry.bind("<KeyRelease>", lambda _: self._on_field_change())

        # Overwrite warning banner
        self.warning_label = ctk.CTkLabel(
            container,
            text="",
            font=FONT_CAPTION,
            text_color=ACCENT_AMBER,
            anchor="w",
        )
        self.warning_label.pack(fill="x", pady=(2, 0))

        self.check_conflicts()

    def _on_browse_folder(self):
        from tkinter import filedialog
        chosen = filedialog.askdirectory(
            title="Choose Output Destination Folder",
            initialdir=self.folder_entry.get().strip(),
            parent=self.winfo_toplevel(),
        )
        if chosen:
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, chosen)
            self._on_field_change()

    def _on_field_change(self):
        self.check_conflicts()
        if self.on_change:
            self.on_change()

    def get_output_path(self) -> Path:
        folder = self.folder_entry.get().strip()
        filename = self.filename_entry.get().strip()
        return Path(folder) / filename

    def set_defaults(self, folder: str, filename: str):
        self.folder_entry.delete(0, "end")
        self.folder_entry.insert(0, folder)
        self.filename_entry.delete(0, "end")
        self.filename_entry.insert(0, filename)
        self.check_conflicts()

    def check_conflicts(self) -> bool:
        """Checks if destination file already exists."""
        try:
            out_p = self.get_output_path()
            if out_p.exists():
                self.warning_label.configure(
                    text="⚠️ Output file already exists. You will be prompted before overwriting.",
                    text_color=ACCENT_AMBER,
                )
                return True
            else:
                self.warning_label.configure(text="")
                return False
        except Exception:
            self.warning_label.configure(text="")
            return False


class StatsCard(ctk.CTkFrame):
    """
    Shows real compression/decompression results with clean metric cards,
    space savings percentage, and 'Show in Folder' button.
    """

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=BG_SURFACE,
            border_color=BORDER_DEFAULT,
            border_width=1,
            corner_radius=CORNER_RADIUS_LG,
            **kwargs,
        )
        self.last_output_path: Optional[str] = None
        self._build_ui()

    def _build_ui(self):
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=16)

        # Header with badge and Show in Folder button
        header_row = ctk.CTkFrame(self.container, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 12))

        self.title_lbl = ctk.CTkLabel(
            header_row,
            text="Operation Summary",
            font=FONT_HEADING,
            text_color=TEXT_PRIMARY,
        )
        self.title_lbl.pack(side="left")

        self.status_badge = ctk.CTkLabel(
            header_row,
            text="✓ Success",
            font=FONT_BADGE,
            text_color=ACCENT_GREEN,
            fg_color=BG_INPUT,
            corner_radius=CORNER_RADIUS_SM,
        )
        self.status_badge.pack(side="left", padx=(10, 0))

        self.open_folder_btn = ctk.CTkButton(
            header_row,
            text="📁 Show in Folder",
            width=120,
            height=30,
            font=FONT_CAPTION,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            corner_radius=CORNER_RADIUS_SM,
            command=self._on_open_folder,
        )
        self.open_folder_btn.pack(side="right")

        # Metric cards row
        self.metrics_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.metrics_frame.pack(fill="x", pady=(0, 10))

        self.m1 = self._create_metric_tile(self.metrics_frame, "Original Size", "-")
        self.m2 = self._create_metric_tile(self.metrics_frame, "Output Size", "-")
        self.m3 = self._create_metric_tile(self.metrics_frame, "Space Saved", "-")
        self.m4 = self._create_metric_tile(self.metrics_frame, "Efficiency", "-")

        self.m1.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.m2.pack(side="left", fill="both", expand=True, padx=3)
        self.m3.pack(side="left", fill="both", expand=True, padx=3)
        self.m4.pack(side="left", fill="both", expand=True, padx=(6, 0))

        # Bottom explanation / notes
        self.note_lbl = ctk.CTkLabel(
            self.container,
            text="",
            font=FONT_CAPTION,
            text_color=TEXT_MUTED,
            anchor="w",
            wraplength=600,
        )
        self.note_lbl.pack(fill="x", pady=(4, 0))

    def _create_metric_tile(self, parent, title: str, value: str) -> ctk.CTkFrame:
        tile = ctk.CTkFrame(
            parent,
            fg_color=BG_INPUT,
            corner_radius=CORNER_RADIUS_MD,
            border_color=BORDER_DEFAULT,
            border_width=1,
        )
        t_lbl = ctk.CTkLabel(
            tile,
            text=title,
            font=FONT_CAPTION,
            text_color=TEXT_MUTED,
        )
        t_lbl.pack(pady=(8, 2), padx=10)

        v_lbl = ctk.CTkLabel(
            tile,
            text=value,
            font=FONT_SUBHEADING,
            text_color=TEXT_PRIMARY,
        )
        v_lbl.pack(pady=(0, 8), padx=10)

        tile.value_label = v_lbl  # type: ignore
        return tile

    def display_compression_result(self, orig_size: int, comp_size: int, output_path: str):
        self.last_output_path = output_path
        self.title_lbl.configure(text="Compression Completed")
        self.status_badge.configure(text="✓ Compressed", text_color=ACCENT_GREEN)

        saved = orig_size - comp_size
        pct = (saved / orig_size * 100.0) if orig_size > 0 else 0.0

        self.m1.value_label.configure(text=format_size(orig_size))  # type: ignore
        self.m2.value_label.configure(text=format_size(comp_size))  # type: ignore

        if saved >= 0:
            self.m3.value_label.configure(text=format_size(saved), text_color=ACCENT_GREEN)  # type: ignore
            self.m4.value_label.configure(text=f"{pct:.1f}% saved", text_color=ACCENT_GREEN)  # type: ignore
            self.note_lbl.configure(
                text=f"Lossless Huffman compression saved {format_size(saved)} ({pct:.2f}% reduction)."
            )
        else:
            abs_increase = abs(saved)
            inc_pct = abs(pct)
            self.m3.value_label.configure(text=f"+{format_size(abs_increase)}", text_color=ACCENT_AMBER)  # type: ignore
            self.m4.value_label.configure(text=f"+{inc_pct:.1f}% (overhead)", text_color=ACCENT_AMBER)  # type: ignore
            self.note_lbl.configure(
                text="Note: Small files (<2 KB) or high-entropy data can increase in size due to the 2,061-byte frequency table header required by the Huffman decoder."
            )

    def display_decompression_result(self, restored_size: int, output_path: str):
        self.last_output_path = output_path
        self.title_lbl.configure(text="Decompression Completed")
        self.status_badge.configure(text="✓ Restored", text_color=ACCENT_GREEN)

        self.m1.value_label.configure(text="Huffman (.huff)")  # type: ignore
        self.m2.value_label.configure(text=format_size(restored_size))  # type: ignore
        self.m3.value_label.configure(text="Byte-for-Byte Exact", text_color=ACCENT_CYAN)  # type: ignore
        self.m4.value_label.configure(text="100% Restored", text_color=ACCENT_GREEN)  # type: ignore

        self.note_lbl.configure(
            text=f"Original file successfully restored ({format_size(restored_size)}). Bitstream decoded losslessly."
        )

    def _on_open_folder(self):
        if self.last_output_path:
            open_in_file_manager(self.last_output_path)


class StatusBar(ctk.CTkFrame):
    """
    Status bar at the bottom of the window displaying status, backend engine state,
    and shortcut hints.
    """

    def __init__(self, master, engine_status: str = "Ready", **kwargs):
        super().__init__(
            master,
            fg_color=BG_ROOT,
            border_color=BORDER_DEFAULT,
            border_width=1,
            height=32,
            **kwargs,
        )

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="x", expand=True, padx=16, pady=4)

        self.status_lbl = ctk.CTkLabel(
            self.container,
            text="Ready",
            font=FONT_CAPTION,
            text_color=TEXT_SECONDARY,
            anchor="w",
        )
        self.status_lbl.pack(side="left", fill="x", expand=True)

        self.engine_lbl = ctk.CTkLabel(
            self.container,
            text=f"● {engine_status}",
            font=FONT_CAPTION,
            text_color=ACCENT_GREEN,
        )
        self.engine_lbl.pack(side="right", padx=(16, 0))

        self.hint_lbl = ctk.CTkLabel(
            self.container,
            text="Ctrl+O: Browse | Ctrl+Enter: Run | Ctrl+R: Reset",
            font=FONT_CAPTION,
            text_color=TEXT_MUTED,
        )
        self.hint_lbl.pack(side="right")

    def set_status(self, text: str, is_error: bool = False, is_success: bool = False):
        color = TEXT_SECONDARY
        if is_error:
            color = ACCENT_RED
        elif is_success:
            color = ACCENT_GREEN
        self.status_lbl.configure(text=text, text_color=color)

    def set_engine_status(self, text: str, active: bool = True):
        color = ACCENT_GREEN if active else ACCENT_AMBER
        self.engine_lbl.configure(text=f"● {text}", text_color=color)


class AboutDialog(ctk.CTkToplevel):
    """
    Modal window explaining Huffman Coding in beginner-friendly language,
    with tree structure concepts, algorithmic steps, and technical info.
    """

    def __init__(self, master):
        super().__init__(master)
        self.title("About HuffZip & Huffman Coding")
        self.geometry("640x560")
        self.resizable(False, False)
        self.configure(fg_color=BG_ROOT)

        # Center on parent window
        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        # Header
        top_frame = ctk.CTkFrame(container, fg_color="transparent")
        top_frame.pack(fill="x", pady=(0, 14))

        title = ctk.CTkLabel(
            top_frame,
            text="HuffZip — File Compressor",
            font=FONT_TITLE,
            text_color=TEXT_PRIMARY,
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            top_frame,
            text="High-performance lossless compression powered by C & Huffman Coding",
            font=FONT_SUBTITLE,
            text_color=ACCENT_LIGHT,
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Scrollable content area
        scroll = ctk.CTkScrollableFrame(
            container,
            fg_color=BG_SURFACE,
            corner_radius=CORNER_RADIUS_MD,
            border_color=BORDER_DEFAULT,
            border_width=1,
        )
        scroll.pack(fill="both", expand=True, pady=(0, 16))

        def add_section(heading: str, body: str):
            h = ctk.CTkLabel(
                scroll,
                text=heading,
                font=FONT_SUBHEADING,
                text_color=TEXT_PRIMARY,
                anchor="w",
            )
            h.pack(fill="x", pady=(10, 4), padx=12)

            b = ctk.CTkLabel(
                scroll,
                text=body,
                font=FONT_BODY,
                text_color=TEXT_SECONDARY,
                anchor="w",
                justify="left",
                wraplength=540,
            )
            b.pack(fill="x", pady=(0, 10), padx=12)

        add_section(
            "What is Huffman Coding?",
            "Huffman Coding is a renowned lossless data compression algorithm developed by David A. Huffman in 1952. "
            "Unlike traditional fixed-length representations (where every byte takes 8 bits), Huffman coding assigns "
            "variable-length binary prefix codes to symbols based on their frequency of occurrence."
        )

        add_section(
            "How the Algorithm Works",
            "1. Frequency Analysis: Scans the input file and tallies the counts of all 256 possible byte values.\n"
            "2. Min-Heap Priority Queue: Builds a forest of leaf nodes and repeatedly merges the two lowest-frequency nodes into parent nodes.\n"
            "3. Prefix-Free Code Tree: Traverses left (0) and right (1) branches to generate optimal prefix codes. Frequent characters get tiny 2- to 4-bit codes, while rare ones get longer codes.\n"
            "4. Bitstream Serialization: Replaces original bytes with variable-length bit codes and packages them with the frequency table header."
        )

        add_section(
            "Understanding Header Overhead",
            "The HuffZip (.huff) binary format stores a 256-entry frequency table (2,061 bytes) at the start of every archive so the decoder can reconstruct the exact Huffman tree.\n\n"
            "• Large text & repetitive files: Notice significant size reduction (often 30% to 70% space savings).\n"
            "• Very small files (<2 KB): Output size may increase slightly due to the fixed 2 KB frequency table header.\n"
            "• Compressed binaries (JPEG, ZIP, MP4): Already have high entropy and will not compress further."
        )

        add_section(
            "Architecture & Technologies",
            "• Backend: Custom, modular C engine (huffman.c, heap.c, fileio.c, utils.c) implementing bit-level stream I/O and min-heap queues.\n"
            "• GUI: Python desktop interface built with CustomTkinter and TkinterDnD2 drag-and-drop integration.\n"
            "• Safety: Safe subprocess execution with binary comparison verification."
        )

        # Close button
        close_btn = ctk.CTkButton(
            container,
            text="Close",
            width=100,
            height=34,
            font=FONT_BODY_BOLD,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            corner_radius=CORNER_RADIUS_SM,
            command=self.destroy,
        )
        close_btn.pack(side="right")
