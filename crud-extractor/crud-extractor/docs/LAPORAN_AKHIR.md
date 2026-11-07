# Laporan Akhir

## 1. Hasil evaluasi

```text
Belum berlabel (tidak dievaluasi): pemeliharaan.sql

Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql (20 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.68    0.85   0.76
```

Parser menemukan semua 20 triple tanpa salah-temu. Regex menghasilkan 8 salah-temu (FP) dan
3 terlewat (FN). Ground truth `audit.sql` (10 triple) kami susun dari SPESIFIKASI.md, bukan
dari keluaran program, supaya evaluasi tidak melingkar. `pemeliharaan.sql` belum berlabel
sehingga tidak dihitung. **[ISI: siapa melabeli file lain; status pemeliharaan.sql]**

## 2. Tiga kasus di mana regex salah

1. **Komentar dan string dibaca sebagai SQL** (`laporan_penjualan.sql`).
   Baris 2 `-- DELETE FROM pelanggan` dan baris 6 `o.catatan <> 'FROM rahasia'`. Regex
   menghasilkan `pelanggan` D dan `rahasia` R, padahal keduanya bukan perintah. Lexer
   membuang komentar (SPESIFIKASI 2.3) dan membaca string sebagai satu token `STRING`
   (2.4), sehingga isinya tidak pernah sampai ke parser. Komentar yang sama juga menggeser
   baris: `_START.search` mengambil `DELETE` dari komentar, sehingga triple milik `SELECT`
   di baris 3 jatuh ke baris 2 (2 FP dan 2 FN). Konsep: lexing.

2. **`DELETE FROM` terhitung dua kali** (`audit.sql:16`, `laporan_penjualan.sql:15`,
   `campuran_error.sql:8`).
   `DELETE FROM sesi s WHERE ...` cocok dengan pola `DELETE\s+FROM` (D, benar) dan juga
   pola `FROM` (R, salah): 3 FP. Parser menentukan operasi dari jenis statement (`_delete`
   menghasilkan node `Delete`), sehingga tabel target hanya D. Konsep: parsing; makna
   ditentukan struktur grammar, bukan potongan teks.

3. **Join dengan koma terlewat** (`audit.sql:3`).
   `FROM pelanggan p, pesanan o`: pola `FROM` hanya menangkap satu nama, jadi `pesanan`
   hilang (1 FN). Parser membaca daftar sumber dengan loop `while self._match(T.COMMA)`
   di `_select` (grammar: `table_ref { "," table_ref }`), sehingga semua tabel terbaca.
   Konsep: parsing.

Kasus tambahan: `campuran_error.sql:4` (`SELECT id nama, FROM pesanan`) rusak sintaks.
Parser menolaknya dan tidak menghitungnya (SPESIFIKASI 5 dan 6); regex tetap menghasilkan
`pesanan` R karena tidak mengenal sintaks (1 FP).

## 3. Batas pendekatan kami

1. **Alias tidak terdefinisi** (`audit.sql:18`: `SELECT s.id FROM pengguna u`).
   Alias `s` tidak ada di scope mana pun, jadi resolver melaporkan error (SPESIFIKASI 4.3).
   Tabel `pengguna` tetap tercatat R, tetapi kolom `s.id` tidak bisa dipetakan ke tabel
   mana pun. Untuk memastikan kolom milik tabel siapa dibutuhkan skema database, yang tidak
   dimiliki tool ini.
2. **View, trigger, dan stored procedure** (SPESIFIKASI 9, di luar lingkup).
   `SELECT * FROM v_laporan` dicatat R pada `v_laporan`, padahal itu view; tabel dasarnya
   tidak muncul di CRUD matrix. Trigger yang menulis ke tabel lain saat `INSERT` juga tidak
   terlihat. Dibutuhkan definisi view/trigger dari skema database.
3. **Sintaks di luar subset** (SPESIFIKASI 9: `WITH`, `UNION`, `MERGE`, `t.*`).
   Contoh: `WITH x AS (SELECT ...) SELECT * FROM x`. Statement gagal di-parse sehingga tidak
   dihitung, dan seluruh tabel di dalamnya hilang dari matrix (FN). Dibutuhkan grammar yang
   diperluas.

(Cadangan: SQL yang dirakit di kode aplikasi, mis. `"SELECT * FROM " + tabel`. Tool hanya
membaca teks `.sql`, sehingga tabelnya tidak muncul. Dibutuhkan analisis kode aplikasi
atau log query.)

## 4. Pembagian kerja

- **Arif Habibi Simamora:** Parser dan Analyzer (perbaikan P1, P2, P3, T1, A1 beserta tes
  regresinya), ground truth `audit.sql`, evaluasi (`evaluate.py`), analisis regex,
  `LAPORAN_BUG.md`, serta review Lexer dan Resolver.
- **Ziddan:** Lexer dan Resolver (L1, L2, L3, T3, R1, R2, T2) dan `pemeliharaan.sql`.
  **[ISI oleh Ziddan: detail dan tes regresinya]**
- **Memastikan kami sama-sama paham:** **[ISI hanya yang benar-benar dilakukan]**

AI (Claude) dipakai untuk menyusun draf laporan ini; semua angka dicocokkan dengan keluaran
`evaluate.py` dan isi file SQL. Rinciannya ada di `LOG_AI.md`.