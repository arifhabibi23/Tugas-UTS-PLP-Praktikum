# Laporan Akhir

## 1. Hasil evaluasi

```text
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

Parser menemukan seluruh 27 triple tanpa salah-temu (F1 = 1.00). Regex menghasilkan 12 salah-temu (FP) dan 8 terlewat (FN). Ground truth disusun secara manual berdasarkan aturan SPESIFIKASI.md (bukan dari keluaran program) agar evaluasi tidak melingkar. Seluruh 4 file sampel (audit.sql, campuran_error.sql, laporan_penjualan.sql, dan pemeliharaan.sql) kini telah berlabel lengkap dan dievaluasi secara penuh.

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
4. **Keterbatasan Pendekatan Regex (Baseline)**.
   Regex tidak memiliki *lexer state* dan *symbol table*, sehingga mengekstrak kata kunci SQL di dalam komentar (`/* ... */` atau `--`) dan string literal, yang menyebabkan rendahnya presisi (Precision = 0.65).
(Cadangan: SQL yang dirakit di kode aplikasi, mis. `"SELECT * FROM " + tabel`. Tool hanya
membaca teks `.sql`, sehingga tabelnya tidak muncul. Dibutuhkan analisis kode aplikasi
atau log query.)

## 4. Pembagian kerja

- **Arif Habibi Simamora:** Parser dan Analyzer. Memperbaiki seluruh bug Lexer dan Resolver (L1, L2, L3, T3, R1, R2, T2; semua commit pada `lexer.py` dan `resolver.py` atas nama Arif) beserta tes regresinya. Membersihkan impor tak terpakai di `resolver.py` (`7e48072`).
- **Muhammad Ziddan:** ground truth `pemeliharaan.sql` (7 triple), evaluasi parser vs regex (27 triple), Keputusan 4 (hierarki scope dan shadowing), entri laporan bug L1, L2, R1, serta entri log penggunaan AI.

AI (Claude) dipakai untuk menyusun draf laporan ini; semua angka dicocokkan dengan keluaran
`evaluate.py` dan isi file SQL. Rinciannya ada di `LOG_AI.md`.