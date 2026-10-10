"""
HuffZip Main Desktop Application.
Modern CustomTkinter GUI integrating with the C Huffman Compression backend.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from gui.backend_runner import (
    ensure_backend_executable,
    find_backend_executable,
    run_compress,
    run_decompress,
    validate_huff_header,
)
from gui.components import (
    AboutDialog,
    DropZone,
    OutputConfigCard,
    StatsCard,
    StatusBar,
)
from gui.styles import (
    ACCENT_AMBER,
    ACCENT_GREEN,
    ACCENT_HOVER,
    ACCENT_PRIMARY,
    ACCENT_RED,
    BG_INPUT,
    BG_ROOT,
    BG_SURFACE,
    BG_SURFACE_HOVER,
    BORDER_DEFAULT,
    CORNER_RADIUS_LG,
    CORNER_RADIUS_MD,
    CORNER_RADIUS_SM,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_CAPTION,
    FONT_HEADING,
    FONT_SUBTITLE,
    FONT_TITLE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

# Optional TkinterDnD wrapper support
try:
    from tkinterdnd2 import TkinterDnD

    class BaseAppWindow(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)

    HAS_DND = True
except Exception:
    class BaseAppWindow(ctk.CTk):
        pass

    HAS_DND = False


class HuffZipApp(BaseAppWindow):
    """
    Main HuffZip Desktop Application Window.
    """

    def __init__(self):
        super().__init__()

        # Appearance configuration
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("HuffZip — File Compressor")
        self.geometry("980x760")
        self.minsize(860, 680)
        self.configure(fg_color=BG_ROOT)

        # Application state
        self.is_busy = False
        self.backend_path = None
        self.active_tab = "compress"  # 'compress' or 'decompress'

        # File states
        self.comp_input_file: Optional[Path] = None
        self.decomp_input_file: Optional[Path] = None

        self._check_backend_status()
        self._build_layout()
        self._bind_shortcuts()

    def _check_backend_status(self):
        """Locates backend and verifies engine health."""
        exe = find_backend_executable()
        if not exe:
            exe, _ = ensure_backend_executable()
        self.backend_path = exe

    def _build_layout(self):
        # 1. Header Bar
        self._build_header()

        # 2. Main Navigation (Segmented Switcher)
        self._build_navigation()

        # 3. Main Workspace Container (Holds Compressor & Decompressor Views)
        self.workspace_container = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace_container.pack(fill="both", expand=True, padx=24, pady=(12, 12))

        # View frames
        self.compressor_view = ctk.CTkFrame(self.workspace_container, fg_color="transparent")
        self.decompressor_view = ctk.CTkFrame(self.workspace_container, fg_color="transparent")

        self._build_compressor_view()
        self._build_decompressor_view()

        # 4. Bottom Status Bar (created before switching tabs)
        engine_text = f"C Engine: {self.backend_path.name}" if self.backend_path else "C Engine: Missing (will compile)"
        self.status_bar = StatusBar(self, engine_status=engine_text)
        self.status_bar.pack(side="bottom", fill="x")

        # Show Compressor by default
        self._switch_to_tab("compress")

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color=BG_SURFACE, height=72, corner_radius=0)
        header_frame.pack(fill="x", pady=(0, 0))

        inner = ctk.CTkFrame(header_frame, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=12)

        # Left branding
        brand_box = ctk.CTkFrame(inner, fg_color="transparent")
        brand_box.pack(side="left")

        logo_lbl = ctk.CTkLabel(
            brand_box,
            text="⚡",
            font=("Segoe UI Emoji", 26),
            text_color=ACCENT_PRIMARY,
        )
        logo_lbl.pack(side="left", padx=(0, 10))

        title_box = ctk.CTkFrame(brand_box, fg_color="transparent")
        title_box.pack(side="left")

        app_title = ctk.CTkLabel(
            title_box,
            text="HuffZip — File Compressor",
            font=FONT_TITLE,
            text_color=TEXT_PRIMARY,
        )
        app_title.pack(anchor="w")

        app_sub = ctk.CTkLabel(
            title_box,
            text="Simple, fast, Huffman-powered compression.",
            font=FONT_SUBTITLE,
            text_color=TEXT_MUTED,
        )
        app_sub.pack(anchor="w")

        # Right actions
        actions_box = ctk.CTkFrame(inner, fg_color="transparent")
        actions_box.pack(side="right")

        about_btn = ctk.CTkButton(
            actions_box,
            text="ℹ About Algorithm",
            font=FONT_CAPTION,
            fg_color=BG_SURFACE_HOVER,
            hover_color=ACCENT_HOVER,
            corner_radius=CORNER_RADIUS_SM,
            height=32,
            command=self._open_about_dialog,
        )
        about_btn.pack(side="right", padx=(8, 0))

    def _build_navigation(self):
        nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        nav_frame.pack(fill="x", padx=24, pady=(16, 4))

        self.nav_seg = ctk.CTkSegmentedButton(
            nav_frame,
            values=["🗜️ Compressor", "📂 Decompressor"],
            font=FONT_BODY_BOLD,
            selected_color=ACCENT_PRIMARY,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=BG_SURFACE,
            unselected_hover_color=BG_SURFACE_HOVER,
            height=40,
            corner_radius=CORNER_RADIUS_MD,
            command=self._on_nav_change,
        )
        self.nav_seg.set("🗜️ Compressor")
        self.nav_seg.pack(fill="x")

    def _on_nav_change(self, value: str):
        if "Compressor" in value:
            self._switch_to_tab("compress")
        else:
            self._switch_to_tab("decompress")

    def _switch_to_tab(self, tab: str):
        self.active_tab = tab
        if tab == "compress":
            self.decompressor_view.pack_forget()
            self.compressor_view.pack(fill="both", expand=True)
            self.status_bar.set_status("Compressor active. Drop or select a file to compress.")
        else:
            self.compressor_view.pack_forget()
            self.decompressor_view.pack(fill="both", expand=True)
            self.status_bar.set_status("Decompressor active. Drop or select a .huff file to restore.")

    # ==========================================
    # SECTION A: COMPRESSOR VIEW
    # ==========================================
    def _build_compressor_view(self):
        # Scrollable container for clean responsiveness
        self.comp_scroll = ctk.CTkScrollableFrame(
            self.compressor_view,
            fg_color="transparent",
        )
        self.comp_scroll.pack(fill="both", expand=True)

        # 1. Drop Zone
        self.comp_drop = DropZone(
            self.comp_scroll,
            title="Drop a file here to compress",
            subtitle="or browse files from your computer",
            button_text="Choose File",
            on_file_selected=self._on_comp_file_selected,
            on_file_cleared=self._on_comp_file_cleared,
            is_decompressor=False,
        )
        self.comp_drop.pack(fill="x", pady=(0, 14))

        # 2. Output Configuration Card
        self.comp_output_card = OutputConfigCard(
            self.comp_scroll,
            default_folder="",
            default_filename="",
        )
        self.comp_output_card.pack(fill="x", pady=(0, 14))

        # 3. Action Section
        action_card = ctk.CTkFrame(
            self.comp_scroll,
            fg_color=BG_SURFACE,
            border_color=BORDER_DEFAULT,
            border_width=1,
            corner_radius=CORNER_RADIUS_LG,
        )
        action_card.pack(fill="x", pady=(0, 14))

        action_inner = ctk.CTkFrame(action_card, fg_color="transparent")
        action_inner.pack(fill="x", expand=True, padx=20, pady=16)

        action_row = ctk.CTkFrame(action_inner, fg_color="transparent")
        action_row.pack(fill="x")

        self.comp_btn = ctk.CTkButton(
            action_row,
            text="Compress File",
            font=FONT_BODY_BOLD,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            corner_radius=CORNER_RADIUS_MD,
            height=42,
            state="disabled",
            command=self._start_compression,
        )
        self.comp_btn.pack(side="left", padx=(0, 14))

        self.comp_reset_btn = ctk.CTkButton(
            action_row,
            text="Reset",
            font=FONT_BODY,
            fg_color=BG_INPUT,
            hover_color=BG_SURFACE_HOVER,
            corner_radius=CORNER_RADIUS_MD,
            height=42,
            width=90,
            command=self._on_comp_file_cleared,
        )
        self.comp_reset_btn.pack(side="left")

        self.comp_status_lbl = ctk.CTkLabel(
            action_row,
            text="Please select a file to compress",
            font=FONT_BODY,
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.comp_status_lbl.pack(side="left", fill="x", expand=True, padx=(14, 0))

        # Progress bar
        self.comp_progress = ctk.CTkProgressBar(
            action_inner,
            height=6,
            corner_radius=3,
            progress_color=ACCENT_PRIMARY,
        )
        self.comp_progress.pack(fill="x", pady=(12, 0))
        self.comp_progress.set(0)

        # 4. Statistics Card (initially hidden)
        self.comp_stats_card = StatsCard(self.comp_scroll)

    def _on_comp_file_selected(self, file_path_str: str):
        path = Path(file_path_str)
        self.comp_input_file = path

        # Set suggested output path: <name>.huff in the same directory
        suggested_folder = str(path.parent)
        suggested_filename = f"{path.name}.huff"
        self.comp_output_card.set_defaults(suggested_folder, suggested_filename)

        self.comp_btn.configure(state="normal")
        self.comp_status_lbl.configure(
            text=f"Ready to compress '{path.name}'",
            text_color=TEXT_PRIMARY,
        )
        self.status_bar.set_status(f"Selected: {path.name}")
        self.comp_stats_card.pack_forget()

    def _on_comp_file_cleared(self):
        self.comp_input_file = None
        self.comp_drop.clear_selection(notify=False)
        self.comp_output_card.set_defaults("", "")
        self.comp_btn.configure(state="disabled")
        self.comp_status_lbl.configure(
            text="Please select a file to compress",
            text_color=TEXT_MUTED,
        )
        self.comp_progress.set(0)
        self.comp_stats_card.pack_forget()
        self.status_bar.set_status("Compressor reset.")

    def _start_compression(self):
        if self.is_busy or not self.comp_input_file:
            return

        out_path = self.comp_output_card.get_output_path()

        # Check overwrite confirmation
        if out_path.exists():
            confirm = messagebox.askyesno(
                "Confirm Overwrite",
                f"The destination file already exists:\n\n{out_path}\n\nDo you want to overwrite it?",
                parent=self,
            )
            if not confirm:
                return

        self._set_busy(True, "Preparing file...")
        self.comp_status_lbl.configure(text="Compressing with Huffman C engine...", text_color=TEXT_PRIMARY)
        self.comp_progress.configure(mode="indeterminate")
        self.comp_progress.start()

        # Run compression off main thread
        threading.Thread(
            target=self._worker_compress,
            args=(self.comp_input_file, out_path),
            daemon=True,
        ).start()

    def _worker_compress(self, in_p: Path, out_p: Path):
        res = run_compress(in_p, out_p, backend_exe=self.backend_path)
        self.after(0, self._finish_compression, res)

    def _finish_compression(self, res):
        self._set_busy(False)
        self.comp_progress.stop()
        self.comp_progress.configure(mode="determinate")

        if res.success:
            self.comp_progress.set(1.0)
            self.comp_status_lbl.configure(text="Compression complete!", text_color=ACCENT_GREEN)
            self.status_bar.set_status(
                f"Compressed '{Path(res.input_path).name}' -> '{Path(res.output_path).name}' successfully",
                is_success=True,
            )
            # Display stats card
            self.comp_stats_card.pack(fill="x", pady=(0, 14))
            self.comp_stats_card.display_compression_result(
                res.original_size,
                res.output_size,
                res.output_path,
            )
        else:
            self.comp_progress.set(0)
            self.comp_status_lbl.configure(text="Compression failed", text_color=ACCENT_RED)
            self.status_bar.set_status("Compression failed.", is_error=True)
            messagebox.showerror(
                "Compression Failed",
                f"Error during Huffman compression:\n\n{res.error_message}",
                parent=self,
            )

    # ==========================================
    # SECTION B: DECOMPRESSOR VIEW
    # ==========================================
    def _build_decompressor_view(self):
        self.decomp_scroll = ctk.CTkScrollableFrame(
            self.decompressor_view,
            fg_color="transparent",
        )
        self.decomp_scroll.pack(fill="both", expand=True)

        # 1. Drop Zone
        self.decomp_drop = DropZone(
            self.decomp_scroll,
            title="Drop a compressed file here to decompress",
            subtitle="or browse a .huff file from your computer",
            button_text="Choose Compressed File",
            on_file_selected=self._on_decomp_file_selected,
            on_file_cleared=self._on_decomp_file_cleared,
            allowed_extensions=[".huff"],
            is_decompressor=True,
        )
        self.decomp_drop.pack(fill="x", pady=(0, 14))

        # 2. Output Configuration Card
        self.decomp_output_card = OutputConfigCard(
            self.decomp_scroll,
            default_folder="",
            default_filename="",
        )
        self.decomp_output_card.pack(fill="x", pady=(0, 14))

        # 3. Action Section
        action_card = ctk.CTkFrame(
            self.decomp_scroll,
            fg_color=BG_SURFACE,
            border_color=BORDER_DEFAULT,
            border_width=1,
            corner_radius=CORNER_RADIUS_LG,
        )
        action_card.pack(fill="x", pady=(0, 14))

        action_inner = ctk.CTkFrame(action_card, fg_color="transparent")
        action_inner.pack(fill="x", expand=True, padx=20, pady=16)

        action_row = ctk.CTkFrame(action_inner, fg_color="transparent")
        action_row.pack(fill="x")

        self.decomp_btn = ctk.CTkButton(
            action_row,
            text="Decompress File",
            font=FONT_BODY_BOLD,
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            corner_radius=CORNER_RADIUS_MD,
            height=42,
            state="disabled",
            command=self._start_decompression,
        )
        self.decomp_btn.pack(side="left", padx=(0, 14))

        self.decomp_reset_btn = ctk.CTkButton(
            action_row,
            text="Reset",
            font=FONT_BODY,
            fg_color=BG_INPUT,
            hover_color=BG_SURFACE_HOVER,
            corner_radius=CORNER_RADIUS_MD,
            height=42,
            width=90,
            command=self._on_decomp_file_cleared,
        )
        self.decomp_reset_btn.pack(side="left")

        self.decomp_status_lbl = ctk.CTkLabel(
            action_row,
            text="Please select a compressed .huff file",
            font=FONT_BODY,
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self.decomp_status_lbl.pack(side="left", fill="x", expand=True, padx=(14, 0))

        # Progress bar
        self.decomp_progress = ctk.CTkProgressBar(
            action_inner,
            height=6,
            corner_radius=3,
            progress_color=ACCENT_PRIMARY,
        )
        self.decomp_progress.pack(fill="x", pady=(12, 0))
        self.decomp_progress.set(0)

        # 4. Statistics Card (initially hidden)
        self.decomp_stats_card = StatsCard(self.decomp_scroll)

    def _on_decomp_file_selected(self, file_path_str: str):
        path = Path(file_path_str)
        self.decomp_input_file = path

        # Validate header immediately
        is_valid, _orig_size, val_err = validate_huff_header(path)

        # Derive sensible output filename
        suggested_folder = str(path.parent)
        if path.name.lower().endswith(".huff") and len(path.name) > 5:
            # Strip .huff suffix (e.g. sample.txt.huff -> sample.txt)
            suggested_filename = path.name[:-5]
        else:
            suggested_filename = f"{path.stem}.decompressed"

        # If stripping .huff results in a file with same name in same folder,
        # add .restored if it exists or use restored name
        potential_dest = Path(suggested_folder) / suggested_filename
        if potential_dest.exists() and potential_dest == path:
            suggested_filename = f"{path.stem}.restored"

        self.decomp_output_card.set_defaults(suggested_folder, suggested_filename)

        if is_valid:
            self.decomp_btn.configure(state="normal")
            self.decomp_status_lbl.configure(
                text=f"Valid archive: '{path.name}' ready to extract",
                text_color=TEXT_PRIMARY,
            )
            self.status_bar.set_status(f"Archive verified: {path.name}")
        else:
            self.decomp_btn.configure(state="disabled")
            self.decomp_status_lbl.configure(
                text=f"Invalid format: {val_err}",
                text_color=ACCENT_RED,
            )
            self.status_bar.set_status(f"Invalid archive header: {val_err}", is_error=True)

        self.decomp_stats_card.pack_forget()

    def _on_decomp_file_cleared(self):
        self.decomp_input_file = None
        self.decomp_drop.clear_selection(notify=False)
        self.decomp_output_card.set_defaults("", "")
        self.decomp_btn.configure(state="disabled")
        self.decomp_status_lbl.configure(
            text="Please select a compressed .huff file",
            text_color=TEXT_MUTED,
        )
        self.decomp_progress.set(0)
        self.decomp_stats_card.pack_forget()
        self.status_bar.set_status("Decompressor reset.")

    def _start_decompression(self):
        if self.is_busy or not self.decomp_input_file:
            return

        out_path = self.decomp_output_card.get_output_path()

        if out_path.exists():
            confirm = messagebox.askyesno(
                "Confirm Overwrite",
                f"The destination file already exists:\n\n{out_path}\n\nDo you want to overwrite it?",
                parent=self,
            )
            if not confirm:
                return

        self._set_busy(True, "Preparing archive...")
        self.decomp_status_lbl.configure(text="Decompressing with Huffman C engine...", text_color=TEXT_PRIMARY)
        self.decomp_progress.configure(mode="indeterminate")
        self.decomp_progress.start()

        threading.Thread(
            target=self._worker_decompress,
            args=(self.decomp_input_file, out_path),
            daemon=True,
        ).start()

    def _worker_decompress(self, in_p: Path, out_p: Path):
        res = run_decompress(in_p, out_p, backend_exe=self.backend_path)
        self.after(0, self._finish_decompression, res)

    def _finish_decompression(self, res):
        self._set_busy(False)
        self.decomp_progress.stop()
        self.decomp_progress.configure(mode="determinate")

        if res.success:
            self.decomp_progress.set(1.0)
            self.decomp_status_lbl.configure(text="Decompression complete!", text_color=ACCENT_GREEN)
            self.status_bar.set_status(
                f"Restored '{Path(res.output_path).name}' losslessly ({res.output_size} bytes)",
                is_success=True,
            )
            self.decomp_stats_card.pack(fill="x", pady=(0, 14))
            self.decomp_stats_card.display_decompression_result(
                res.output_size,
                res.output_path,
            )
        else:
            self.decomp_progress.set(0)
            self.decomp_status_lbl.configure(text="Decompression failed", text_color=ACCENT_RED)
            self.status_bar.set_status("Decompression failed.", is_error=True)
            messagebox.showerror(
                "Decompression Failed",
                f"Error during Huffman decompression:\n\n{res.error_message}",
                parent=self,
            )

    # ==========================================
    # COMMON UTILITIES & SHORTCUTS
    # ==========================================
    def _set_busy(self, busy: bool, status_msg: str = ""):
        self.is_busy = busy
        state = "disabled" if busy else "normal"
        self.comp_btn.configure(state=state)
        self.decomp_btn.configure(state=state)
        self.nav_seg.configure(state=state)

        if busy and status_msg:
            self.status_bar.set_status(status_msg)

    def _open_about_dialog(self):
        AboutDialog(self)

    def _bind_shortcuts(self):
        self.bind("<Control-o>", lambda _: self._on_shortcut_open())
        self.bind("<Control-O>", lambda _: self._on_shortcut_open())
        self.bind("<Control-Return>", lambda _: self._on_shortcut_run())
        self.bind("<Control-r>", lambda _: self._on_shortcut_reset())
        self.bind("<Control-R>", lambda _: self._on_shortcut_reset())
        self.bind("<F1>", lambda _: self._open_about_dialog())

    def _on_shortcut_open(self):
        if self.active_tab == "compress":
            self.comp_drop._on_browse_click()
        else:
            self.decomp_drop._on_browse_click()

    def _on_shortcut_run(self):
        if self.active_tab == "compress":
            self._start_compression()
        else:
            self._start_decompression()

    def _on_shortcut_reset(self):
        if self.active_tab == "compress":
            self._on_comp_file_cleared()
        else:
            self._on_decomp_file_cleared()


def main():
    app = HuffZipApp()
    app.mainloop()


if __name__ == "__main__":
    main()
