# 🗜️ caesium-tui

> Antarmuka terminal interaktif berbasis TUI untuk [caesiumclt](https://github.com/Lymphatus/caesium-clt) — kompres gambar dengan navigasi keyboard penuh, tanpa perlu hafal satu pun perintah.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey?style=flat-square" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Dibuat%20oleh-yingtze-blue?style=flat-square" />
</p>

---

## ✨ Apa Ini?

**caesium-tui** adalah *wrapper* interaktif untuk `caesiumclt` yang mengubah deretan opsi CLI yang panjang menjadi wizard langkah-demi-langkah yang nyaman dipakai siapa saja — dari pemula hingga pengguna mahir.

Tidak perlu mengingat flag, tidak perlu buka dokumentasi. Cukup jalankan, navigasi dengan keyboard, dan kompres.

---

## 🎮 Kontrol Keyboard

| Tombol | Aksi |
|--------|------|
| `↑` `↓` | Navigasi menu |
| `Enter` | Pilih / konfirmasi |
| `Space` | Toggle pilihan (multi-select) |
| `←` `→` | Pilih Yes / No di dialog |
| `Esc` / `Q` | Kembali ke langkah sebelumnya |
| `Y` / `N` | Jawab cepat dialog konfirmasi |
| `Backspace` / `Del` | Hapus karakter di kolom input |
| `Home` / `End` | Loncat ke awal / akhir teks |

---

## 🚀 Cara Pakai

### Prasyarat

- Python **3.8+** (sudah tersedia di macOS & Linux modern)
- `caesiumclt` — script akan otomatis mendeteksi dan menawarkan instalasi via Homebrew di macOS

### Jalankan

```bash
python3 caesium_tui.py
```

Tidak perlu instalasi library tambahan. `curses` sudah bawaan Python.

### Instalasi caesiumclt (jika belum ada)

Script akan mendeteksi otomatis. Jika belum terinstal, tersedia pilihan:

```bash
# macOS (Homebrew) — bisa install langsung dari dalam script
brew install caesiumclt

# Linux (Cargo)
cargo install caesiumclt

# Windows (Winget)
winget install SaeraSoft.CaesiumCLT
```

---

## 🧭 Alur Wizard

Wizard terdiri dari **7 langkah** yang bisa dinavigasi maju-mundur:

```
1. Kompresi    →  Mode lossy / lossless / target ukuran
2. Format      →  JPEG, PNG, WebP, atau biarkan seperti aslinya
3. Resize      →  Lebar, tinggi, sisi terpanjang, atau terpendek
4. Metadata    →  Simpan EXIF dan/atau tanggal file asli
5. Lanjutan    →  Threads, min savings, chroma subsampling, dry run
6. Input       →  File atau folder + rekursif + pertahankan struktur
7. Output      →  Folder tujuan + kebijakan overwrite
```

Sebelum dieksekusi, seluruh konfigurasi ditampilkan di **layar ringkasan** lengkap dengan preview perintah yang akan dijalankan.

---

## 🖥️ Tampilan

```
┌─────────────────────────────────────────────────────┐
│ ⚡ CAESIUM CLT  ▸  Kompresi                          │
│                                                      │
│   ▶ 🔍  Lossy — atur kualitas (0–100)               │
│     💎  Lossless — tanpa kehilangan kualitas        │
│     📏  Target ukuran maksimum file                 │
│                                                      │
│ ──────────────────────────────────────────────────  │
│  ↑↓ Navigasi   Enter Pilih   Esc Kembali            │
└─────────────────────────────────────────────────────┘
```

---

## 📋 Fitur Lengkap

- **Auto-detect** `caesiumclt` di PATH sistem
- **Auto-install** via Homebrew di macOS (dengan konfirmasi)
- **Navigasi penuh** dengan keyboard — tanpa klik, tanpa mouse
- **Wizard multi-langkah** dengan navigasi maju & mundur
- **Multi-select** dengan `Space` untuk opsi metadata
- **Input editor** dengan kursor, backspace, dan delete
- **Dialog Yes/No** yang responsif
- **Preview perintah** di layar ringkasan sebelum eksekusi
- **Output langsung** di terminal — tidak disembunyikan dari pengguna
- **Ulang tanpa restart** setelah kompresi selesai

---

## 🗂️ Struktur Proyek

```
caesium-tui/
├── caesium_tui.py   # Script utama
├── README.md
├── CHANGELOG.md
└── LICENSE
```

---

## 🤝 Kontribusi

Pull request, laporan bug, dan saran fitur sangat diterima. Buka [issue baru](../../issues) atau fork dan kirim PR langsung.

---

## 📄 Lisensi

Didistribusikan di bawah [MIT License](LICENSE). Bebas digunakan, dimodifikasi, dan didistribusikan.

---

<p align="center">
  Dibuat dengan ☕ oleh <a href="https://github.com/yingtze">yingtze</a>
  <br/>
  Didukung oleh <a href="https://github.com/Lymphatus/caesium-clt">caesiumclt</a> dari Lymphatus
</p>
