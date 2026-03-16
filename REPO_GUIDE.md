# 📦 Panduan Publikasi Repo — caesium-tui

---

## 1. Saran Nama Repo

Pilih salah satu yang paling sesuai dengan selera:

| Nama | Karakter |
|------|----------|
| `caesium-tui` | ✅ Direkomendasikan — bersih, deskriptif, mudah dicari |
| `caesiumclt-interactive` | Eksplisit, cocok untuk SEO GitHub |
| `caesium-wizard` | Lebih kasual, menonjolkan aspek wizard-nya |
| `imgcompress-tui` | Lebih generik, berguna jika nanti support tool lain |

**Rekomendasi:** `caesium-tui` — singkat, langsung ke poin, dan mudah diingat.

---

## 2. Deskripsi Repo (untuk kolom "About" di GitHub)

> Antarmuka terminal interaktif (TUI) untuk caesiumclt — kompres gambar JPEG, PNG, dan WebP dengan navigasi keyboard penuh, tanpa perlu hafal satu pun perintah CLI.

*(maks. ~350 karakter, pas untuk kolom About GitHub)*

---

## 3. Saran Tags / Topics GitHub

Salin dan tempel di kolom **Topics** di halaman repo:

```
caesium  image-compression  tui  cli  python  terminal  curses  interactive
jpeg  png  webp  macos  linux  image-optimizer  command-line-tool
```

**Tips:** GitHub Topics membantu discoverability — pilih yang relevan, jangan isi semua.

---

## 4. Saran Commit Message

### Commit pertama (initial)
```
feat: initial release — interactive TUI wizard for caesiumclt
```

### Commit file dokumentasi
```
docs: add README, CHANGELOG, and LICENSE
```

### Kalau commit semua sekaligus dalam satu commit
```
feat: add caesium_tui.py with full keyboard-driven wizard

- 7-step interactive wizard (compression, format, resize, metadata,
  advanced, input, output)
- Full keyboard navigation: arrow keys, Enter, Space, Esc
- Auto-detect and Homebrew install for caesiumclt on macOS
- Summary screen with command preview before execution
- Inline text editor with cursor, backspace, Home/End support
- Yes/No dialogs with left/right navigation
```

### Commit-commit berikutnya (referensi)
```
fix: handle missing input path gracefully in step_input
refactor: extract draw_box into shared helper module
feat: add config profile save/load
docs: update CHANGELOG for v1.1.0
chore: bump version to 1.1.0
```

---

## 5. Teks Deskripsi Lengkap (untuk README bagian atas atau bio)

Versi pendek (1 baris):
> TUI wrapper untuk caesiumclt — kompres gambar dari terminal dengan navigasi keyboard.

Versi sedang (3 baris):
> caesium-tui mengubah antarmuka CLI caesiumclt yang penuh flag menjadi wizard interaktif
> yang nyaman dipakai siapa saja. Navigasi dengan tombol panah, toggle opsi dengan Space,
> dan lihat preview perintah sebelum dieksekusi — semua tanpa meninggalkan terminal.

Versi panjang (untuk deskripsi di README):
> Mengompres gambar dari terminal seharusnya tidak butuh membaca halaman dokumentasi.
> caesium-tui hadir sebagai jembatan antara kekuatan caesiumclt dan kemudahan pakai
> sehari-hari — melalui antarmuka TUI berbasis curses yang berjalan di Python bawaan
> sistem, tanpa dependensi eksternal, dengan navigasi keyboard penuh yang intuitif.
