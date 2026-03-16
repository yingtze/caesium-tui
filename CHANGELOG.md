# Catatan Perubahan

Semua perubahan penting pada proyek ini didokumentasikan di sini.

Format mengacu pada [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
dan proyek ini mengikuti [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2025-03-16

### 🎉 Rilis Perdana

Rilis pertama **caesium-tui** — antarmuka terminal interaktif untuk `caesiumclt`.

### Ditambahkan

- Wizard interaktif 7 langkah: Kompresi, Format, Resize, Metadata, Lanjutan, Input, Output
- Navigasi keyboard penuh: tombol panah, `Enter`, `Space`, `Esc`
- Deteksi otomatis binary `caesiumclt` di PATH sistem
- Instalasi otomatis via Homebrew untuk pengguna macOS
- Petunjuk instalasi manual untuk Linux dan Windows
- Mode kompresi: lossy (quality), lossless, dan target ukuran maksimum
- Pilihan format output: JPEG, PNG, WebP, atau biarkan seperti aslinya
- Opsi resize: lebar, tinggi, sisi terpanjang, sisi terpendek, dengan perlindungan upscale
- Toggle metadata via multi-select: EXIF dan tanggal file
- Pengaturan lanjutan: jumlah thread, min savings, chroma subsampling JPEG, dry run
- Input editor satu baris dengan kursor penuh (backspace, delete, Home, End)
- Dialog Yes/No dengan navigasi `←→` dan shortcut `Y`/`N`
- Layar ringkasan konfigurasi sebelum eksekusi dengan preview perintah lengkap
- Output eksekusi langsung di terminal tanpa buffer tersembunyi
- Opsi untuk mengulang kompresi setelah selesai tanpa restart script
- Dukungan platform: macOS, Linux, Windows

---

## [Belum Dirilis]

### Direncanakan

- Simpan dan muat profil konfigurasi favorit
- Riwayat kompresi terakhir
- Progress bar per file saat kompresi batch
- Dukungan bahasa tambahan (English)
- Mode non-interaktif via argumen CLI untuk integrasi pipeline
