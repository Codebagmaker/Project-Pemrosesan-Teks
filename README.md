# Project-Pemrosesan-Teks

Klasifikasi Multi-Kelas Emosi Publik pada Komentar Liputan Video Demonstrasi 10 November Yogyakarta menggunakan perbandingan ekstraksi fitur TF-IDF dan FastText dengan algoritma Naive Bayes, XGBoost, dan Bi-LSTM.

## Struktur Proyek

| File | Fungsi |
|---|---|
| `01_scrape_youtube.py` | Pengumpulan komentar dari 5 video YouTube |
| `02_preprocess.py` | Pembersihan teks dan deduplikasi |
| `03_annotation.py` | Pelabelan emosi oleh 2 anotator, Cohen's Kappa, adjudikasi |
| `04_experiments.py` | 5 eksperimen klasifikasi dan evaluasi |
| `requirements.txt` | Daftar library Python |

## 1. Pengumpulan Data (`01_scrape_youtube.py`)

Data berupa komentar publik pada 5 video liputan Demonstrasi 10 November Yogyakarta di YouTube. Komentar diambil melalui **YouTube Data API v3**, yaitu jalur resmi dari YouTube.

**Proses:**
1. ID video diambil dari tautan YouTube (video biasa maupun Shorts).
2. Komentar utama (*top-level*) diambil halaman demi halaman.
3. Balasan komentar (*replies*) ikut diambil secara default (dapat dimatikan dengan `--no-replies`).
4. Komentar dengan ID yang sama dihapus agar tidak ganda.
5. Hasil disimpan ke `data/comments_raw.csv`.

**Kolom keluaran:** `comment_id`, `video_no`, `video_id`, `parent_id`, `is_reply`, `text_raw`, `like_count`, `published_at`.

**Privasi:** nama pengguna dan identitas akun tidak disimpan. Penelitian hanya menggunakan isi komentar.

**Cara menjalankan:**
```bash
# set API key terlebih dahulu (PowerShell)
$env:YOUTUBE_API_KEY="API_KEY_ANDA"
python 01_scrape_youtube.py
```

Skrip mencetak jumlah komentar per video dan total, sebagai pembanding dengan jumlah komentar yang tampil di YouTube saat pencatatan (775, 2.120, 399, 3.116, dan 207; total 6.617). Selisih kecil dapat terjadi karena komentar dihapus atau disembunyikan.

## 2. Pembersihan Data (`02_preprocess.py`)

Pembersihan dirancang agar **informasi emosi tidak hilang**.

**Tahapan:**
1. **Hapus URL dan mention** (`@username`).
2. **Case folding:** semua huruf diubah menjadi huruf kecil.
3. **Konversi emoji menjadi token teks** (contoh: `emoji_wajah_marah`), bukan dibuang, karena emoji membawa sinyal emosi.
4. **Hapus tanda baca dan karakter khusus.**
5. **Reduksi huruf berulang** (contoh: `marahhhh` menjadi `marahh`).
6. **Normalisasi slang dan singkatan** menggunakan kamus (`yg` menjadi `yang`, `gk` menjadi `tidak`, dst.). Kamus dapat diperluas melalui `data/slang_dict.csv` (kolom `slang,formal`).
7. **Penghapusan stopword (opsional)** dengan `--remove-stopwords`. Kata negasi seperti *tidak* dan *bukan* tetap dipertahankan.
8. **Hapus komentar kosong** setelah pembersihan.
9. **Deduplikasi** berdasarkan teks bersih, dilakukan sebelum pembagian data untuk mencegah *data leakage* antara data latih dan data uji.

Stemming tidak digunakan karena dapat merusak kata slang dan representasi subword FastText.

**Cara menjalankan:**
```bash
python 02_preprocess.py
python 02_preprocess.py --slang data/slang_dict.csv   # dengan kamus slang tambahan
```

**Keluaran:** `data/comments_clean.csv` dengan kolom `comment_id`, `video_no`, `text_raw`, `text_clean`.

## Instalasi

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
