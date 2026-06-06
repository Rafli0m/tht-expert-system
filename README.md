# THT Expert System

Aplikasi sistem pakar diagnosis awal penyakit THT berbasis Flask dengan metode Certainty Factor.

## Fitur

- Diagnosis awal 5 penyakit THT berdasarkan gejala.
- Perhitungan nilai keyakinan menggunakan Certainty Factor.
- Simulasi langkah perhitungan CF.
- Halaman dataset, daftar penyakit, metode, dan referensi.

## Menjalankan Project

Install dependency:

```bash
pip install -r requirements.txt
```

Jalankan aplikasi:

```bash
python app.py
```

Buka aplikasi di browser:

```text
http://127.0.0.1:5000
```

## Struktur Utama

- `app.py` - aplikasi Flask dan logika Certainty Factor.
- `templates/` - halaman HTML.
- `static/` - aset CSS dan gambar.
- `dataset/` - dataset penyakit dan gejala.
- `jurnal/` - referensi jurnal.
