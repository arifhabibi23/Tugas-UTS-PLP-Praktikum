# Laporan Bug

## Bug 1: Presedensi AND/OR sama tingkat (P1)

**Ditemukan oleh:** Arif Habibi Simamora · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** `a = 1 OR b = 2 AND c = 3` terbaca `(a OR b) AND c`: akar pohon WHERE
bernilai `AND`. SPESIFIKASI.md bagian 3.1: `AND` lebih kuat dari `OR`, sehingga
akarnya seharusnya `OR` dengan anak kanan `AND`.

**Reproduksi minimal.**

```sql
SELECT id FROM t WHERE a = 1 OR b = 2 AND c = 3
```

**Akar masalah.** Kode lama membaca AND dan OR dalam satu loop yang sama, jadi A OR B AND C 
digabung dari kiri: (A OR B) dulu, baru di-AND dengan C. Seharusnya B AND C yang menyatu lebih dulu. 
Di recursive descent, presedensi dibuat lewat lapisan fungsi: operator yang lebih kuat ada di fungsi 
yang lebih dalam, sehingga menangkap operandnya lebih awal. Kode lama hanya punya satu lapisan untuk 
dua operator (Crafting Interpreters, bab 6).

**Perbaikan.** `crud/parser.py`: `_logical()` dipecah menjadi `_or()` (hanya `OR`) yang
memanggil `_and()` (hanya `AND`) yang memanggil `_not()`; `_expr()` kini memanggil `_or()`.
Alternatif: tabel presedensi dengan precedence climbing (Pratt parser). Tidak dipilih karena 
seluruh parser sudah memakai gaya satu-fungsi-per-tingkat ';' mengganti satu bagian dengan gaya lain 
membuat kode tidak seragam.

**Test regresi.** `test_regresi_p1_presedensi_and_lebih_kuat_dari_or`: gagal di `bb12f84`
(`assert 'AND' == 'OR'`), lulus di `6370de0`. `test_regresi_p1_not_lebih_kuat_dari_and`
lulus di kedua versi (pengaman; `_not()` sudah benar sejak awal).

**Peran AI.** (lihat bagian "Peran AI" di bawah)

---

## Bug 2: Error recovery tidak berhenti di `;` (P2)

**Ditemukan oleh:** Arif Habibi Simamora · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** Setelah satu statement rusak, statement valid sesudahnya hilang. Hasil `1 0`
(1 error, 0 statement); SPESIFIKASI.md bagian 6 meminta `1 1`.

**Reproduksi minimal.**

```sql
SELEKT x; SELECT id FROM t;
```

**Akar masalah.** Setelah ada error, parser harus membuang token sampai menemukan titik aman 
agar bisa lanjut membaca statement berikutnya. Di SQL titik aman itu ';'. Kode lama tidak berhenti
di ';', jadi ia membuang semuanya sampai akhir file dan statement valid sesudah error ikut hilang. 
Ini disebut panic mode dengan synchronize (Crafting Interpreters, bab 6).

**Perbaikan.** `crud/parser.py`, `_synchronize`: loop kini `return` setelah mengonsumsi token
`SEMICOLON`. Berhenti *setelah* `;` (bukan sebelum) karena `;` milik statement yang rusak;
kalau berhenti sebelum, `parse_script` akan melihat `;` dan statement berikutnya mulai dari
posisi yang sama. Alternatif: menjadikan keyword awal statement (SELECT, INSERT, dst.) sebagai 
titik sinkronisasi. Tidak dipilih karena kata itu bisa muncul di dalam subquery, dan spesifikasi 
bagian 6 menyebut ; secara eksplisit.

**Test regresi.** `test_regresi_p2_synchronize_berhenti_setelah_titik_koma`: gagal di
`84da599` (`statements` kosong), lulus di `39b9b5c`.

Bukti: `SELEKT x; SELECT id FROM t;` memberi `1 error, 0 statement` di `84da599` dan
`1 error, 1 statement` di HEAD.

**Peran AI.** (lihat bagian "Peran AI" di bawah)

---

## Bug 3: `LEFT OUTER JOIN` ditolak (P3)

**Ditemukan oleh:** Arif Habibi Simamora · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** `ParseError: Baris 1, kolom 25: diharapkan JOIN, ditemukan 'OUTER'`.
SPESIFIKASI.md bagian 3: `join = [ "INNER" | "LEFT" [ "OUTER" ] ] "JOIN" ...`.

**Reproduksi minimal.**

```sql
SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id
```

**Akar masalah.** Di grammar, OUTER itu opsional. Kode lama setelah LEFT langsung mewajibkan 
JOIN, jadi OUTER dianggap token yang salah tempat. Perbaikannya memakai match (cek kalau ada,
lewati kalau tidak), bukan expect (wajib ada). Masalahnya: kode parser tidak sejalan dengan
grammar, padahal tiap bagian grammar harus punya padanan di kode (bab 6).

**Perbaikan.** `crud/parser.py`, fungsi pemroses `join`: ditambah `self._match_kw("OUTER")`
setelah `LEFT`. Memakai `match` (opsional), bukan `expect` (wajib), karena `LEFT JOIN` tanpa
`OUTER` tetap valid. Alternatif: membuat LEFT OUTER sebagai satu token di lexer. Tidak dipilih 
karena mengubah kontrak lexer (spesifikasi bagian 2.1) hanya untuk satu kasus parser.

**Test regresi.** `test_regresi_p3_left_outer_join_diterima`: gagal di `4d9aac9`, lulus di `84da599`.

**Peran AI.** (lihat bagian "Peran AI" di bawah)

---

## Bug 4: `INSERT ... SELECT` belum didukung (T1)

**Ditemukan oleh:** Arif Habibi Simamora · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** `ParseError: INSERT ... SELECT belum didukung, ditemukan 'SELECT'`.
SPESIFIKASI.md bagian 3 (`insert_stmt`) dan bagian 5 (tabel target C, tabel sumber R).

**Reproduksi minimal.**

```sql
INSERT INTO arsip (id) SELECT id FROM pesanan
```

**Akar masalah.** Grammar insert_stmt punya dua bentuk: VALUES atau SELECT. Kode lama hanya
mengerjakan bentuk pertama, dan bentuk kedua berisi TODO yang langsung melempar error. Jadi 
input yang sah menurut grammar ditolak. Parser harus menerima semua kalimat yang bisa dihasilkan grammar (bab 6).

**Perbaikan.** `crud/parser.py`, `_insert`: cabang `SELECT` diganti dengan `self._select()`
dan `ast.Insert(table, columns, [], query, ...)`. `SELECT` di sini membuat scope sendiri
(spesifikasi 4.1) dan diproses analyzer seperti subquery biasa. Alternatif: memperlakukan INSERT ... SELECT 
sebagai statement terpisah dengan node AST baru. Tidak dipilih karena node Insert sudah punya field query.

**Test regresi.** `test_regresi_t1_insert_select_diterima`: gagal di `7e48072`, lulus di `d7cc1f6`.

**Peran AI.** (lihat bagian "Peran AI" di bawah)

---

## Bug 5: Subquery di UPDATE dibaca sebagai U (A1)

**Ditemukan oleh:** Arif Habibi Simamora · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** Hasil `{'a': {'U'}, 'b': {'U'}}`; yang diharapkan `{'a': {'U'}, 'b': {'R'}}`.
SPESIFIKASI.md bagian 5: membaca tabel lewat subquery selalu R.

**Reproduksi minimal.**

```sql
UPDATE a SET x = 1 WHERE id IN (SELECT a_id FROM b)
```

**Akar masalah.** Parsing-nya sudah benar; kesalahannya ada di analyzer. Analyzer menelusuri 
pohon sambil membawa “mode” (U atau R) ke bawah. Kode lama menurunkan mode U ke seluruh SET dan 
WHERE, sehingga tabel di dalam subquery ikut dianggap diubah, padahal hanya dibaca. Perbaikannya 
menurunkan mode R ke ekspresi, dan hanya tabel target yang U. Konsepnya adalah traversal AST dengan
konteks yang diwariskan, serta pemisahan parsing dari analisis (bab 5 dan 11).

**Perbaikan.** `crud/analyzer.py`, `analyze_statement`: `_collect(..., "U")` untuk ekspresi
`SET` dan `WHERE` diubah menjadi `"R"`; hanya tabel target yang `U`. Alternatif: menandai node 
subquery di parser. Tidak dipilih karena parser tidak boleh memuat keputusan CRUD 
(SPESIFIKASI.md bagian 7, batasan arsitektur).

**Test regresi.** `test_regresi_a1_subquery_update_hanya_target_yang_u`: gagal di
`b138b7c~1`, lulus di `b138b7c`.

**Peran AI.** (lihat bagian "Peran AI" di bawah)

---

## Peran AI (untuk semua bug di atas)

AI (Claude) dipakai selama pengerjaan untuk: menyusun ground truth `audit.sql` dari
SPESIFIKASI.md; memverifikasi bahwa tes regresi gagal pada kode sebelum perbaikan (kode lama
diekstrak dengan `git archive` ke folder terpisah lalu dijalankan dengan pytest); menemukan
bahwa tes `NOT` untuk P1 ternyata lolos di kode lama sehingga kami mengoreksi komentar tes;
serta membantu menyusun draf laporan ini, termasuk penjelasan "Akar masalah" dalam bahasa
lisan, yang kemudian kami baca, cocokkan dengan kode dan buku, dan sesuaikan.
Patch pertama T1 kami tulis sendiri dan salah (membuat 20 tes gagal), lalu kami perbaiki
setelah menjalankan pytest penuh. Verifikasi: semua klaim "gagal sebelum, lulus sesudah"
berasal dari output pytest yang kami jalankan sendiri pada commit lama dan baru.