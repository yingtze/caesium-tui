#!/usr/bin/env python3
"""
caesium_tui.py — Interactive TUI for caesiumclt
Navigasi: Arrow Keys ↑↓  |  Enter = pilih/konfirmasi  |  Space = toggle
          Esc/Q = kembali/keluar  |  Tab = pindah field
Requires: Python 3.8+, caesiumclt (auto-detect / auto-install via Homebrew)
"""

import curses
import os
import sys
import shutil
import subprocess
import platform
import textwrap
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Config:
    # Compression
    mode: str = "quality"          # quality | lossless | maxsize
    quality: str = "80"
    max_size: str = "512000"
    # Format
    fmt: str = "original"          # original | jpeg | png | webp
    # Resize
    resize_mode: str = ""          # "" | width | height | long-edge | short-edge
    resize_value: str = ""
    no_upscale: bool = False
    # Metadata
    keep_exif: bool = False
    keep_dates: bool = False
    # Advanced
    jpeg_subsampling: str = "auto"
    threads: str = "0"
    min_savings: str = ""
    dry_run: bool = False
    # IO
    inputs: list = field(default_factory=list)
    recursive: bool = False
    keep_structure: bool = False
    output_mode: str = "folder"    # folder | same
    output_path: str = "./output"
    suffix: str = ""
    overwrite: str = "all"

# ─────────────────────────────────────────────────────────────────────────────
# COLOR PAIRS
# ─────────────────────────────────────────────────────────────────────────────

# pair indices
P_NORMAL    = 1
P_HIGHLIGHT = 2
P_TITLE     = 3
P_DIM       = 4
P_GREEN     = 5
P_RED       = 6
P_YELLOW    = 7
P_CYAN      = 8
P_HEADER    = 9
P_SELECTED  = 10
P_BORDER    = 11

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(P_NORMAL,    curses.COLOR_WHITE,   -1)
    curses.init_pair(P_HIGHLIGHT, curses.COLOR_BLACK,   curses.COLOR_CYAN)
    curses.init_pair(P_TITLE,     curses.COLOR_CYAN,    -1)
    curses.init_pair(P_DIM,       8,                    -1)
    curses.init_pair(P_GREEN,     curses.COLOR_GREEN,   -1)
    curses.init_pair(P_RED,       curses.COLOR_RED,     -1)
    curses.init_pair(P_YELLOW,    curses.COLOR_YELLOW,  -1)
    curses.init_pair(P_CYAN,      curses.COLOR_CYAN,    -1)
    curses.init_pair(P_HEADER,    curses.COLOR_BLACK,   curses.COLOR_BLUE)
    curses.init_pair(P_SELECTED,  curses.COLOR_GREEN,   -1)
    curses.init_pair(P_BORDER,    curses.COLOR_BLUE,    -1)

# ─────────────────────────────────────────────────────────────────────────────
# DRAWING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def safe_addstr(win, y, x, text, attr=curses.A_NORMAL):
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x < 0:
        return
    avail = w - x - 1
    if avail <= 0:
        return
    try:
        win.addstr(y, x, text[:avail], attr)
    except curses.error:
        pass

def draw_box(win, y, x, h, w, color=P_BORDER, title=""):
    attr = curses.color_pair(color)
    # corners & sides
    try:
        win.attron(attr)
        win.addch(y,     x,     curses.ACS_ULCORNER)
        win.addch(y,     x+w-1, curses.ACS_URCORNER)
        win.addch(y+h-1, x,     curses.ACS_LLCORNER)
        win.addch(y+h-1, x+w-1, curses.ACS_LRCORNER)
        for i in range(1, w-1):
            win.addch(y,     x+i, curses.ACS_HLINE)
            win.addch(y+h-1, x+i, curses.ACS_HLINE)
        for i in range(1, h-1):
            win.addch(y+i, x,     curses.ACS_VLINE)
            win.addch(y+i, x+w-1, curses.ACS_VLINE)
        win.attroff(attr)
    except curses.error:
        pass
    if title:
        safe_addstr(win, y, x+2, f" {title} ",
                    curses.color_pair(P_TITLE) | curses.A_BOLD)

def draw_header(win, title, subtitle=""):
    h, w = win.getmaxyx()
    try:
        win.attron(curses.color_pair(P_HEADER) | curses.A_BOLD)
        win.addstr(0, 0, " " * w)
        win.addstr(0, 2, f"⚡ CAESIUM CLT  ▸  {title}"[:w-3])
        win.attroff(curses.color_pair(P_HEADER) | curses.A_BOLD)
    except curses.error:
        pass
    if subtitle:
        safe_addstr(win, 1, 2, subtitle, curses.color_pair(P_DIM))

def draw_footer(win, hints: list[tuple[str,str]]):
    h, w = win.getmaxyx()
    parts = []
    for key, desc in hints:
        parts.append(f" {key} ")
        parts.append(f"{desc}  ")
    x = 2
    try:
        win.attron(curses.color_pair(P_DIM))
        win.addstr(h-1, 0, "─" * (w-1))
        win.attroff(curses.color_pair(P_DIM))
    except curses.error:
        pass
    for i, part in enumerate(parts):
        attr = (curses.color_pair(P_HIGHLIGHT) | curses.A_BOLD) if i % 2 == 0 \
               else curses.color_pair(P_DIM)
        if x + len(part) >= w - 1:
            break
        safe_addstr(win, h-1, x, part, attr)
        x += len(part)

# ─────────────────────────────────────────────────────────────────────────────
# GENERIC MENU (arrow key navigation)
# ─────────────────────────────────────────────────────────────────────────────

def menu(win, title: str, subtitle: str, options: list[tuple[str,str]],
         current: str = "", footer_hints=None) -> str | None:
    """
    Full-screen arrow-key menu.
    Returns selected key, or None if Esc/Q pressed.
    """
    idx = next((i for i,(k,_) in enumerate(options) if k == current), 0)
    if footer_hints is None:
        footer_hints = [("↑↓","Navigasi"),("Enter","Pilih"),("Esc","Kembali")]

    while True:
        win.erase()
        h, w = win.getmaxyx()
        draw_header(win, title, subtitle)
        draw_footer(win, footer_hints)

        # Box
        bx, by = 3, 3
        bw = w - 6
        bh = h - 6
        draw_box(win, by, bx, bh, bw, P_BORDER)

        max_visible = bh - 2
        scroll = max(0, idx - max_visible + 1)

        for i, (key, label) in enumerate(options):
            row = i - scroll
            if row < 0 or row >= max_visible:
                continue
            y = by + 1 + row
            prefix = "  "
            attr = curses.color_pair(P_NORMAL)
            if i == idx:
                attr = curses.color_pair(P_HIGHLIGHT) | curses.A_BOLD
                prefix = "▶ "
                safe_addstr(win, y, bx+1, " " * (bw-2), attr)
            safe_addstr(win, y, bx+2, f"{prefix}{label}", attr)

        win.refresh()
        k = win.getch()

        if k in (curses.KEY_UP, ord('k')):
            idx = (idx - 1) % len(options)
        elif k in (curses.KEY_DOWN, ord('j')):
            idx = (idx + 1) % len(options)
        elif k in (curses.KEY_ENTER, 10, 13):
            return options[idx][0]
        elif k in (27, ord('q'), ord('Q')):
            return None
        elif k in (ord('1') + i for i in range(len(options))):
            n = k - ord('0') - 1
            if 0 <= n < len(options):
                return options[n][0]

# ─────────────────────────────────────────────────────────────────────────────
# TOGGLE MENU (Space to toggle multiple, Enter to confirm)
# ─────────────────────────────────────────────────────────────────────────────

def toggle_menu(win, title: str, subtitle: str,
                options: list[tuple[str,str]],
                selected: set[str] | None = None) -> set[str] | None:
    """Multi-select with Space. Returns set of selected keys."""
    if selected is None:
        selected = set()
    idx = 0
    footer_hints = [("↑↓","Navigasi"),("Space","Toggle"),("Enter","Konfirmasi"),("Esc","Batal")]

    while True:
        win.erase()
        h, w = win.getmaxyx()
        draw_header(win, title, subtitle)
        draw_footer(win, footer_hints)
        bx, by = 3, 3
        bw = w - 6
        bh = h - 6
        draw_box(win, by, bx, bh, bw, P_BORDER)
        max_visible = bh - 2
        scroll = max(0, idx - max_visible + 1)
        for i, (key, label) in enumerate(options):
            row = i - scroll
            if row < 0 or row >= max_visible:
                continue
            y = by + 1 + row
            checked = "●" if key in selected else "○"
            line = f"  {checked}  {label}"
            attr = curses.color_pair(P_NORMAL)
            if i == idx:
                attr = curses.color_pair(P_HIGHLIGHT) | curses.A_BOLD
                safe_addstr(win, y, bx+1, " " * (bw-2), attr)
            if key in selected and i != idx:
                attr = curses.color_pair(P_GREEN) | curses.A_BOLD
            safe_addstr(win, y, bx+2, line, attr)
        win.refresh()
        k = win.getch()
        if k in (curses.KEY_UP, ord('k')):
            idx = (idx - 1) % len(options)
        elif k in (curses.KEY_DOWN, ord('j')):
            idx = (idx + 1) % len(options)
        elif k == ord(' '):
            key = options[idx][0]
            if key in selected:
                selected.discard(key)
            else:
                selected.add(key)
        elif k in (curses.KEY_ENTER, 10, 13):
            return selected
        elif k in (27, ord('q')):
            return None

# ─────────────────────────────────────────────────────────────────────────────
# TEXT INPUT (inline editor with backspace, arrow, delete)
# ─────────────────────────────────────────────────────────────────────────────

def text_input(win, prompt: str, default: str = "",
               hint: str = "", validate=None) -> str | None:
    """
    Single-line text input with full cursor navigation.
    Returns entered text, or None if Esc pressed.
    """
    buf = list(default)
    cursor = len(buf)
    error_msg = ""
    footer_hints = [("Enter","Konfirmasi"),("Esc","Batal"),("←→","Gerak cursor")]

    while True:
        win.erase()
        h, w = win.getmaxyx()
        draw_header(win, "Input", prompt)
        draw_footer(win, footer_hints)

        bx, by = 3, 3
        bw = w - 6
        bh = 9
        draw_box(win, by, bx, bh, bw, P_BORDER, "✏  Input")

        # Prompt
        safe_addstr(win, by+2, bx+3, prompt, curses.color_pair(P_CYAN) | curses.A_BOLD)

        # Hint
        if hint:
            safe_addstr(win, by+3, bx+3, hint, curses.color_pair(P_DIM))

        # Input field box
        field_y = by + 5
        field_x = bx + 3
        field_w = bw - 6
        safe_addstr(win, field_y - 1, field_x, "┌" + "─"*(field_w) + "┐",
                    curses.color_pair(P_DIM))
        safe_addstr(win, field_y,     field_x, "│", curses.color_pair(P_DIM))
        safe_addstr(win, field_y,     field_x + field_w + 1, "│", curses.color_pair(P_DIM))
        safe_addstr(win, field_y + 1, field_x, "└" + "─"*(field_w) + "┘",
                    curses.color_pair(P_DIM))

        # Buffer text
        display = "".join(buf)
        scroll_x = max(0, cursor - field_w + 2)
        visible = display[scroll_x: scroll_x + field_w]
        safe_addstr(win, field_y, field_x+1, " " * field_w,
                    curses.color_pair(P_NORMAL) | curses.A_UNDERLINE)
        safe_addstr(win, field_y, field_x+1, visible,
                    curses.color_pair(P_NORMAL) | curses.A_BOLD)

        # Error
        if error_msg:
            safe_addstr(win, field_y+2, bx+3, f"⚠  {error_msg}",
                        curses.color_pair(P_RED))

        # Cursor
        cx = field_x + 1 + (cursor - scroll_x)
        try:
            win.move(field_y, min(cx, w-2))
        except curses.error:
            pass
        curses.curs_set(1)
        win.refresh()

        k = win.getch()
        curses.curs_set(0)

        if k in (curses.KEY_ENTER, 10, 13):
            result = "".join(buf)
            if validate:
                msg = validate(result)
                if msg:
                    error_msg = msg
                    continue
            return result
        elif k == 27:
            return None
        elif k in (curses.KEY_BACKSPACE, 127, 8):
            if cursor > 0:
                buf.pop(cursor - 1)
                cursor -= 1
        elif k == curses.KEY_DC:
            if cursor < len(buf):
                buf.pop(cursor)
        elif k == curses.KEY_LEFT:
            cursor = max(0, cursor - 1)
        elif k == curses.KEY_RIGHT:
            cursor = min(len(buf), cursor + 1)
        elif k == curses.KEY_HOME:
            cursor = 0
        elif k == curses.KEY_END:
            cursor = len(buf)
        elif 32 <= k <= 126:
            buf.insert(cursor, chr(k))
            cursor += 1
        error_msg = ""

# ─────────────────────────────────────────────────────────────────────────────
# YES / NO DIALOG
# ─────────────────────────────────────────────────────────────────────────────

def yesno_dialog(win, title: str, message: str, default: bool = True) -> bool:
    """Left/Right arrow or Y/N to choose."""
    choice = 0 if default else 1  # 0=Yes, 1=No

    while True:
        win.erase()
        h, w = win.getmaxyx()
        draw_header(win, title)
        draw_footer(win, [("←→","Pilih"),("Enter","Konfirmasi"),("Y/N","Langsung pilih")])

        bw = min(50, w - 8)
        bh = 9
        bx = (w - bw) // 2
        by = (h - bh) // 2
        draw_box(win, by, bx, bh, bw, P_BORDER, title)

        # Message (wrapped)
        lines = textwrap.wrap(message, bw - 4)
        for i, line in enumerate(lines[:4]):
            safe_addstr(win, by+2+i, bx+2, line, curses.color_pair(P_NORMAL))

        # Buttons
        btn_y = by + bh - 2
        yes_attr = (curses.color_pair(P_HIGHLIGHT) | curses.A_BOLD) if choice == 0 \
                   else (curses.color_pair(P_GREEN))
        no_attr  = (curses.color_pair(P_HIGHLIGHT) | curses.A_BOLD) if choice == 1 \
                   else (curses.color_pair(P_RED))

        btn_x = bx + bw//2 - 10
        safe_addstr(win, btn_y, btn_x,      "  ✔ Ya   ", yes_attr)
        safe_addstr(win, btn_y, btn_x + 12, "  ✖ Tidak  ", no_attr)

        win.refresh()
        k = win.getch()

        if k in (curses.KEY_LEFT, curses.KEY_RIGHT, 9):
            choice = 1 - choice
        elif k in (curses.KEY_ENTER, 10, 13):
            return choice == 0
        elif k in (ord('y'), ord('Y')):
            return True
        elif k in (ord('n'), ord('N'), 27):
            return False

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY / REVIEW SCREEN
# ─────────────────────────────────────────────────────────────────────────────

def summary_screen(win, cfg: Config, cmd: list[str]) -> str:
    """Shows config summary + command. Returns 'run'|'edit'|'quit'."""
    scroll = 0

    lines = [
        ("Compression Mode",  cfg.mode.upper()),
    ]
    if cfg.mode == "quality":
        lines.append(("Quality", cfg.quality))
    elif cfg.mode == "maxsize":
        lines.append(("Max Size", cfg.max_size))

    lines += [
        ("Output Format",     cfg.fmt),
        ("Resize",            f"{cfg.resize_mode} {cfg.resize_value}".strip() or "—"),
        ("No Upscale",        "✔" if cfg.no_upscale else "—"),
        ("Keep EXIF",         "✔" if cfg.keep_exif else "—"),
        ("Keep Dates",        "✔" if cfg.keep_dates else "—"),
        ("Threads",           cfg.threads),
        ("Min Savings",       cfg.min_savings or "—"),
        ("Dry Run",           "✔" if cfg.dry_run else "—"),
        ("Input",             ", ".join(cfg.inputs) or "—"),
        ("Recursive",         "✔" if cfg.recursive else "—"),
        ("Keep Structure",    "✔" if cfg.keep_structure else "—"),
        ("Output",            cfg.output_path if cfg.output_mode=="folder" else "(same as input)"),
        ("Suffix",            cfg.suffix or "—"),
        ("Overwrite Policy",  cfg.overwrite),
    ]

    cmd_str = " ".join(
        f'"{a}"' if " " in a else a for a in cmd
    )

    footer_hints = [("R","Jalankan"),("E","Edit ulang"),("Q","Keluar"),("↑↓","Scroll")]

    while True:
        win.erase()
        h, w = win.getmaxyx()
        draw_header(win, "Ringkasan Konfigurasi", "Periksa sebelum menjalankan")
        draw_footer(win, footer_hints)

        bx, by = 2, 2
        bw = w - 4
        bh = h - 4
        draw_box(win, by, bx, bh, bw, P_BORDER, "📋 Summary")

        max_visible = bh - 2
        all_lines = lines + [("", ""), ("Command", cmd_str)]
        for i, (k, v) in enumerate(all_lines):
            row = i - scroll
            if row < 0 or row >= max_visible:
                continue
            yy = by + 1 + row
            if not k:
                safe_addstr(win, yy, bx+2, "─" * (bw-4), curses.color_pair(P_DIM))
                continue
            safe_addstr(win, yy, bx+3, f"{k:<20}", curses.color_pair(P_DIM))
            vattr = curses.color_pair(P_CYAN) | curses.A_BOLD
            if k == "Command":
                vattr = curses.color_pair(P_YELLOW) | curses.A_BOLD
            safe_addstr(win, yy, bx+24,
                        v[:bw-26] if len(v) > bw-26 else v, vattr)

        # RUN button hint at bottom of box
        btn_y = by + bh - 2
        safe_addstr(win, btn_y, bx+3,
                    "  ▶  Tekan R untuk JALANKAN  ",
                    curses.color_pair(P_GREEN) | curses.A_BOLD)

        win.refresh()
        k = win.getch()
        if k in (ord('r'), ord('R'), curses.KEY_ENTER, 10, 13):
            return "run"
        elif k in (ord('e'), ord('E')):
            return "edit"
        elif k in (ord('q'), ord('Q'), 27):
            return "quit"
        elif k == curses.KEY_UP:
            scroll = max(0, scroll - 1)
        elif k == curses.KEY_DOWN:
            scroll = min(len(all_lines) - max_visible, scroll + 1)

# ─────────────────────────────────────────────────────────────────────────────
# INSTALL SCREEN (non-curses, called before curses starts)
# ─────────────────────────────────────────────────────────────────────────────

ANSI_RESET  = "\033[0m"
ANSI_BOLD   = "\033[1m"
ANSI_RED    = "\033[91m"
ANSI_GRN    = "\033[92m"
ANSI_YLW    = "\033[93m"
ANSI_CYN    = "\033[96m"
ANSI_DIM    = "\033[2m"

def plain_print(text="", color=""):
    end = ANSI_RESET if color else ""
    print(f"{color}{text}{end}")

def check_and_install() -> str:
    binary = shutil.which("caesiumclt")
    if binary:
        try:
            v = subprocess.run([binary, "--version"], capture_output=True, text=True)
            plain_print(f"  ✔  caesiumclt ditemukan: {binary}", ANSI_GRN)
            plain_print(f"     {v.stdout.strip()}", ANSI_DIM)
        except Exception:
            pass
        input(f"\n{ANSI_DIM}  Tekan Enter untuk melanjutkan...{ANSI_RESET}")
        return binary

    plain_print(f"\n  ✖  caesiumclt TIDAK ditemukan!", ANSI_RED)
    system = platform.system()
    plain_print()

    if system == "Darwin":
        plain_print("  Cara install di macOS:", ANSI_CYN)
        plain_print(f"    {ANSI_DIM}brew install caesiumclt{ANSI_RESET}   (Homebrew)")
        plain_print(f"    {ANSI_DIM}cargo install caesiumclt{ANSI_RESET}  (Cargo/Rust)")
        plain_print()
        choice = input(f"  {ANSI_BOLD}Install otomatis via Homebrew? [y/N]{ANSI_RESET}: ").strip().lower()
        if choice == "y":
            if shutil.which("brew"):
                plain_print("\n  Menginstall...", ANSI_YLW)
                result = subprocess.run(["brew", "install", "caesiumclt"])
                if result.returncode == 0:
                    binary = shutil.which("caesiumclt")
                    if binary:
                        plain_print("  ✔  Berhasil diinstall!", ANSI_GRN)
                        input(f"\n{ANSI_DIM}  Tekan Enter untuk melanjutkan...{ANSI_RESET}")
                        return binary
            else:
                plain_print("  Homebrew tidak ditemukan. Install Homebrew dulu:", ANSI_RED)
                plain_print('  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"', ANSI_DIM)
    elif system == "Linux":
        plain_print("  Cara install di Linux:", ANSI_CYN)
        plain_print(f"    {ANSI_DIM}cargo install caesiumclt{ANSI_RESET}")
        plain_print(f"    atau download dari: https://github.com/Lymphatus/caesium-clt/releases")
    else:
        plain_print("  Cara install di Windows:", ANSI_CYN)
        plain_print(f"    {ANSI_DIM}winget install SaeraSoft.CaesiumCLT{ANSI_RESET}")

    plain_print("\n  Install dulu lalu jalankan script ini kembali.", ANSI_YLW)
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# BUILD CONFIG — WIZARD STEPS
# ─────────────────────────────────────────────────────────────────────────────

def step_compression(win, cfg: Config) -> bool:
    # Mode
    result = menu(win, "Kompresi", "Pilih mode kompresi", [
        ("quality",  "🔍  Lossy — atur kualitas (0–100)"),
        ("lossless", "💎  Lossless — tanpa kehilangan kualitas"),
        ("maxsize",  "📏  Target ukuran maksimum file"),
    ], cfg.mode)
    if result is None:
        return False
    cfg.mode = result

    if result == "quality":
        def validate_q(v):
            if not v.isdigit() or not (0 <= int(v) <= 100):
                return "Masukkan angka 0–100"
        val = text_input(win, "Nilai Kualitas (0–100)", cfg.quality,
                         "Rekomendasi: 70–85 untuk web, 90+ untuk arsip",
                         validate=validate_q)
        if val is None:
            return False
        cfg.quality = val

    elif result == "maxsize":
        val = text_input(win, "Ukuran Maksimum", cfg.max_size,
                         "Contoh: 512000 (bytes)  |  500KB  |  1MB")
        if val is None:
            return False
        cfg.max_size = val
    return True


def step_format(win, cfg: Config) -> bool:
    result = menu(win, "Format Output", "Pilih format output gambar", [
        ("original", "🔄  Sama seperti input (tidak diubah)"),
        ("jpeg",     "📷  Konversi ke JPEG"),
        ("png",      "🖼   Konversi ke PNG"),
        ("webp",     "🌐  Konversi ke WebP"),
    ], cfg.fmt)
    if result is None:
        return False
    cfg.fmt = result
    return True


def step_resize(win, cfg: Config) -> bool:
    result = menu(win, "Resize", "Pilih mode resize (atau skip)", [
        ("",           "⏭   Tidak resize (skip)"),
        ("width",      "↔   Lebar tertentu (jaga aspek rasio)"),
        ("height",     "↕   Tinggi tertentu (jaga aspek rasio)"),
        ("long-edge",  "↗   Sisi terpanjang"),
        ("short-edge", "↙   Sisi terpendek"),
    ], cfg.resize_mode or "")
    if result is None:
        return False
    cfg.resize_mode = result

    if result:
        labels = {
            "width": "Lebar (pixel)",
            "height": "Tinggi (pixel)",
            "long-edge": "Ukuran sisi terpanjang (pixel)",
            "short-edge": "Ukuran sisi terpendek (pixel)",
        }
        val = text_input(win, labels[result], cfg.resize_value or "",
                         "Masukkan ukuran dalam pixel, contoh: 1920")
        if val is None:
            return False
        cfg.resize_value = val
        cfg.no_upscale = yesno_dialog(win, "No Upscale",
                                       "Cegah upscaling jika gambar sudah lebih kecil?",
                                       default=cfg.no_upscale)
    return True


def step_metadata(win, cfg: Config) -> bool:
    opts = [
        ("exif",  "🏷   Simpan EXIF metadata"),
        ("dates", "🕒  Simpan tanggal file asli"),
    ]
    current = set()
    if cfg.keep_exif:  current.add("exif")
    if cfg.keep_dates: current.add("dates")
    result = toggle_menu(win, "Metadata",
                          "Space = toggle  |  Enter = konfirmasi", opts, current)
    if result is None:
        return False
    cfg.keep_exif  = "exif"  in result
    cfg.keep_dates = "dates" in result
    return True


def step_advanced(win, cfg: Config) -> bool:
    # Threads
    val = text_input(win, "Jumlah Thread Paralel", cfg.threads,
                     "0 = otomatis (maksimum CPU)  |  contoh: 4")
    if val is None:
        return False
    cfg.threads = val or "0"

    # Min savings
    val = text_input(win, "Minimum Penghematan (opsional)", cfg.min_savings,
                     "Contoh: 5%  |  100KB  |  kosongkan untuk melewati")
    if val is None:
        return False
    cfg.min_savings = val

    # JPEG subsampling (hanya jika format jpeg/original)
    if cfg.fmt in ("jpeg", "original") and cfg.mode != "lossless":
        result = menu(win, "JPEG Chroma Subsampling",
                      "Opsional — pengaruhi kualitas warna JPEG", [
                ("auto",  "auto  — biarkan encoder memilih (default)"),
                ("4:4:4", "4:4:4 — kualitas warna tertinggi"),
                ("4:2:2", "4:2:2 — seimbang"),
                ("4:2:0", "4:2:0 — ukuran kecil (umum di web)"),
                ("4:1:1", "4:1:1 — kompresi tinggi"),
            ], cfg.jpeg_subsampling)
        if result is None:
            return False
        cfg.jpeg_subsampling = result

    # Dry run
    cfg.dry_run = yesno_dialog(win, "Dry Run",
                                "Simulasi saja tanpa menulis file output?",
                                default=cfg.dry_run)
    return True


def step_input(win, cfg: Config) -> bool:
    val = text_input(
        win,
        "File / Folder Input",
        " ".join(cfg.inputs),
        "Pisah dengan spasi. Contoh: ~/Photos  atau  img1.jpg img2.png",
        validate=lambda v: "Tidak boleh kosong" if not v.strip() else None
    )
    if val is None:
        return False

    inputs = [str(Path(p).expanduser()) for p in val.split()]
    missing = [p for p in inputs if not Path(p).exists()]

    if missing:
        msg = f"Path tidak ditemukan: {', '.join(missing)}"
        yesno_dialog(win, "⚠ Path Tidak Ditemukan", msg + "\n\nLanjutkan tetap?", False)
        inputs = [p for p in inputs if Path(p).exists()]
        if not inputs:
            return False

    cfg.inputs = inputs

    # Recursive?
    has_dir = any(Path(p).is_dir() for p in inputs)
    if has_dir:
        cfg.recursive = yesno_dialog(win, "Rekursif",
                                      "Proses subfolder secara rekursif?",
                                      default=cfg.recursive)
        if cfg.recursive:
            cfg.keep_structure = yesno_dialog(win, "Pertahankan Struktur",
                                              "Pertahankan struktur folder di output?",
                                              default=cfg.keep_structure)
    return True


def step_output(win, cfg: Config) -> bool:
    dest = menu(win, "Tujuan Output", "Pilih folder output", [
        ("folder", "📁  Simpan ke folder tertentu"),
        ("same",   "♻️   Folder yang sama dengan input"),
    ], cfg.output_mode)
    if dest is None:
        return False
    cfg.output_mode = dest

    if dest == "folder":
        val = text_input(win, "Path Folder Output", cfg.output_path,
                         "Folder akan dibuat jika belum ada")
        if val is None:
            return False
        cfg.output_path = val
    else:
        confirmed = yesno_dialog(win, "⚠ Peringatan",
                                  "Mode ini BISA menimpa file asli tanpa suffix! Lanjutkan?",
                                  default=False)
        if not confirmed:
            return False
        val = text_input(win, "Suffix Nama File (opsional)", cfg.suffix,
                         "Contoh: _compressed  |  kosongkan jika tidak perlu")
        if val is None:
            return False
        cfg.suffix = val

    # Overwrite policy
    ow = menu(win, "Kebijakan Overwrite",
              "Jika file output sudah ada", [
        ("all",    "📝  Selalu timpa"),
        ("never",  "🔒  Jangan pernah timpa"),
        ("bigger", "📉  Timpa hanya jika file lama lebih besar"),
    ], cfg.overwrite)
    if ow is None:
        return False
    cfg.overwrite = ow
    return True


# ─────────────────────────────────────────────────────────────────────────────
# BUILD CMD FROM CONFIG
# ─────────────────────────────────────────────────────────────────────────────

def build_cmd(binary: str, cfg: Config) -> list[str]:
    cmd = [binary]

    # Compression
    if cfg.mode == "quality":
        cmd += ["-q", cfg.quality]
    elif cfg.mode == "lossless":
        cmd.append("--lossless")
    elif cfg.mode == "maxsize":
        cmd += ["--max-size", cfg.max_size]

    # Format
    if cfg.fmt != "original":
        cmd += ["--format", cfg.fmt]

    # Resize
    if cfg.resize_mode:
        cmd += [f"--{cfg.resize_mode}", cfg.resize_value]
        if cfg.no_upscale:
            cmd.append("--no-upscale")

    # Metadata
    if cfg.keep_exif:
        cmd.append("-e")
    if cfg.keep_dates:
        cmd.append("--keep-dates")

    # Advanced
    if cfg.threads and cfg.threads != "0":
        cmd += ["--threads", cfg.threads]
    if cfg.min_savings:
        cmd += ["--min-savings", cfg.min_savings]
    if cfg.jpeg_subsampling and cfg.jpeg_subsampling != "auto" \
       and cfg.fmt in ("jpeg", "original") and cfg.mode != "lossless":
        cmd += ["--jpeg-chroma-subsampling", cfg.jpeg_subsampling]
    if cfg.dry_run:
        cmd.append("--dry-run")

    # Recursive
    if cfg.recursive:
        cmd.append("-R")
    if cfg.keep_structure:
        cmd.append("-S")

    # Input
    cmd += cfg.inputs

    # Output
    if cfg.output_mode == "folder":
        cmd += ["-o", cfg.output_path]
    else:
        cmd.append("--same-folder-as-input")
        if cfg.suffix:
            cmd += ["--suffix", cfg.suffix]

    # Overwrite
    cmd += ["-O", cfg.overwrite]

    return cmd


# ─────────────────────────────────────────────────────────────────────────────
# EXECUTION SCREEN (non-curses — real subprocess output)
# ─────────────────────────────────────────────────────────────────────────────

def run_cmd(cmd: list[str]):
    """Run outside curses so user sees live output."""
    curses.endwin()
    cmd_str = " ".join(f'"{a}"' if " " in a else a for a in cmd)
    plain_print("\n" + "─"*60, ANSI_DIM)
    plain_print("  PERINTAH:", ANSI_CYN)
    plain_print(f"  {cmd_str}", ANSI_YLW)
    plain_print("─"*60 + "\n", ANSI_DIM)

    result = subprocess.run(cmd)

    plain_print("\n" + "─"*60, ANSI_DIM)
    if result.returncode == 0:
        plain_print("  ✔  Selesai! Kompresi berhasil.", ANSI_GRN)
    else:
        plain_print(f"  ✖  Error (kode: {result.returncode})", ANSI_RED)
    plain_print("─"*60, ANSI_DIM)
    input(f"\n{ANSI_DIM}  Tekan Enter untuk kembali ke menu...{ANSI_RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN WIZARD
# ─────────────────────────────────────────────────────────────────────────────

STEPS = [
    ("Kompresi",         step_compression),
    ("Format",           step_format),
    ("Resize",           step_resize),
    ("Metadata",         step_metadata),
    ("Lanjutan",         step_advanced),
    ("Input",            step_input),
    ("Output",           step_output),
]

def wizard(win, binary: str):
    curses.curs_set(0)
    init_colors()
    cfg = Config()
    step = 0
    total = len(STEPS)

    while True:
        # Splash / step indicator
        win.erase()
        h, w = win.getmaxyx()

        # Splash screen if step == 0 (before start)
        if step == 0:
            # Show main menu
            action = menu(win, "Menu Utama",
                          "Selamat datang di Caesium Interactive TUI", [
                ("start", "▶   Mulai konfigurasi kompresi"),
                ("quit",  "✖   Keluar"),
            ])
            if action in (None, "quit"):
                return
            # Start wizard

        name, fn = STEPS[step]
        # Step header indicator
        subtitle = f"Langkah {step+1}/{total}: {name}"
        ok = fn(win, cfg)
        if ok:
            step += 1
        elif step > 0:
            step -= 1  # go back
        else:
            # Esc on step 0 → back to main menu
            step = 0
            continue

        if step >= total:
            # All steps done → summary
            cmd = build_cmd(binary, cfg)
            while True:
                action = summary_screen(win, cfg, cmd)
                if action == "run":
                    run_cmd(cmd)
                    # After run, ask again
                    again = yesno_dialog(win, "Selesai",
                                         "Kompresi gambar lain?", default=False)
                    if again:
                        cfg = Config()
                        step = 0
                        break
                    else:
                        return
                elif action == "edit":
                    step = total - 1  # back to last step
                    break
                else:
                    return


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

BANNER = f"""
{ANSI_BOLD}{ANSI_CYN}
  ██████╗ █████╗ ███████╗███████╗██╗██╗   ██╗███╗   ███╗
 ██╔════╝██╔══██╗██╔════╝██╔════╝██║██║   ██║████╗ ████║
 ██║     ███████║█████╗  ███████╗██║██║   ██║██╔████╔██║
 ██║     ██╔══██║██╔══╝  ╚════██║██║██║   ██║██║╚██╔╝██║
 ╚██████╗██║  ██║███████╗███████║██║╚██████╔╝██║ ╚═╝ ██║
  ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝
{ANSI_RESET}{ANSI_DIM}  Interactive TUI — caesiumclt Image Compressor
  Navigasi: ↑↓ Arrow  |  Enter=Pilih  |  Space=Toggle  |  Esc=Kembali
{ANSI_RESET}
"""

def main():
    print(BANNER)
    binary = check_and_install()
    try:
        curses.wrapper(lambda win: wizard(win, binary))
    except KeyboardInterrupt:
        pass
    finally:
        curses.endwin()
        plain_print("\n  Sampai jumpa! 👋\n", ANSI_GRN)


if __name__ == "__main__":
    main()
