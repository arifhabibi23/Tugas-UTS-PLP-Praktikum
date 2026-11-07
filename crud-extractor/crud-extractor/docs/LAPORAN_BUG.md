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

## Peran AI (Bug 1-5)

AI (Claude) dipakai selama pengerjaan untuk: menyusun ground truth `audit.sql` dari
SPESIFIKASI.md; memverifikasi bahwa tes regresi gagal pada kode sebelum perbaikan (kode lama
diekstrak dengan `git archive` ke folder terpisah lalu dijalankan dengan pytest); menemukan
bahwa tes `NOT` untuk P1 ternyata lolos di kode lama sehingga kami mengoreksi komentar tes;
serta membantu menyusun draf laporan ini, termasuk penjelasan "Akar masalah" dalam bahasa
lisan, yang kemudian kami baca, cocokkan dengan kode dan buku, dan sesuaikan.
Patch pertama T1 kami tulis sendiri dan salah (membuat 20 tes gagal), lalu kami perbaiki
setelah menjalankan pytest penuh. Verifikasi: semua klaim "gagal sebelum, lulus sesudah"
berasal dari output pytest yang kami jalankan sendiri pada commit lama dan baru.

---

## Bug 6: Kata Kunci SQL Peka Huruf Besar/Kecil (L1)

**Ditemukan oleh:** Muhammad Ziddan · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** `select id from t` menghasilkan token `select` sebagai `TokenType.IDENT`, bukan `TokenType.KEYWORD`.

**Reproduksi minimal.**

```sql
select id from t
```

**Akar masalah.** Scanner pada lexer mencocokkan kata kunci pada kamus `KEYWORDS` tanpa menormalkan kapitalisasi huruf (*case-sensitive lookup*). SPESIFIKASI.md bagian 2.2 menyatakan kata kunci SQL bersifat *case-insensitive*. Berdasarkan konsep *Scanning* (Crafting Interpreters bab 4), *reserved words* harus dinormalisasi saat penentuan tipe token, tanpa mengubah teks asli token.

**Perbaikan.** `crud/lexer.py` (`9b54346`): lookup kamus memakai `KEYWORDS.get(text.upper(), TokenType.IDENT)`.

**Test regresi.** `test_l1_keyword_huruf_kecil_dikenali` dan `test_l1_keyword_dinormalisasi_ke_huruf_besar` (`9920417`): gagal di `9b54346~1` (2 failed, 1 passed), lulus di HEAD. `test_l1_identifier_tetap_huruf_asli` adalah pengaman.

---

## Bug 7: Komentar Blok Multiline `/* ... */` Melempar LexError (T3)

**Ditemukan oleh:** Muhammad Ziddan · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** `/* komentar */ SELECT` melempar `LexError: komentar blok belum didukung`.

**Reproduksi minimal.**

```sql
/* komentar
dua baris */ SELECT id FROM t
```

**Akar masalah.** *State machine* scanner belum punya transisi untuk karakter `/` yang diikuti `*` (SPESIFIKASI.md bagian 2.3). Ketika pola `/*` terdeteksi, lexer harus memindai karakter sampai menemukan penutup `*/` sambil terus memperbarui penghitung `line` dan `col` (Crafting Interpreters bab 4).

**Perbaikan.** `crud/lexer.py` (`4f5ea3c`): cabang baru di `_scan_token()` yang mengonsumsi karakter sampai pasangan `*/` ditemukan.

**Test regresi.** `test_t3_komentar_blok_dilewati`, `test_t3_komentar_blok_banyak_baris_menjaga_nomor_baris`, dan `test_t3_komentar_blok_tidak_ditutup` (`aef54a3`): ketiganya gagal di `4f5ea3c~1` (3 failed), lulus di HEAD.

---

## Bug 8: Kolom Tanpa Kualifikasi Tidak Di-resolve (T2)

**Ditemukan oleh:** Muhammad Ziddan · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** Query `SELECT nama FROM pelanggan` menghasilkan `ColumnRef.resolved = None`. Pada subquery, kolom tanpa qualifier juga tidak di-resolve, dan kolom ambigu tidak menghasilkan warning.

**Reproduksi minimal.**

```sql
SELECT nama FROM pelanggan p JOIN pesanan o ON o.pelanggan_id = p.id
```

**Akar masalah.** Cabang kolom tanpa qualifier di `resolver.py` hanya berisi `pass` dengan komentar TODO (SPESIFIKASI.md bagian 4.3), sehingga `resolved` tidak pernah terisi dan tidak ada diagnostik. Menurut konsep *Lexical Scoping and Binding* (Crafting Interpreters bab 11), referensi tanpa qualifier harus diikat ke *environment* terdalam.

**Perbaikan.** `crud/resolver.py` (`4d9aac9`): jika scope terdalam berisi tepat satu tabel, `col.resolved` diisi tabel itu. Jika lebih dari satu, dihasilkan warning "ambigu tanpa skema". Jika tidak ada tabel, dihasilkan warning.

**Test regresi.** `test_t2_kolom_tanpa_qualifier_scope_terdalam` dan `test_t2_kolom_tanpa_qualifier_ambigu_beri_warning` (`dc60627`): keduanya gagal di `4d9aac9~1` (2 failed), lulus di HEAD.

---

## Bug 9: Operator `<>` Terbaca Dua Token (L2)

**Ditemukan oleh:** Arif Habibi Simamora · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** `a <> b` dipecah menjadi `<` dan `>`, sehingga parser gagal.

**Reproduksi minimal.**

```sql
SELECT id FROM t WHERE a <> b
```

**Akar masalah.** Lexer tidak melihat karakter berikutnya saat membaca `<`, jadi `<>` tidak digabung menjadi satu operator.

**Perbaikan.** `crud/lexer.py` (`3a5b329`): `<` yang diikuti `>` dikenali sebagai satu token.

**Test regresi.** `test_l2_operator_tidak_sama_satu_token` (`323e914`): gagal di `3a5b329~1`, lulus di HEAD. `test_l2_operator_lain_tidak_berubah` adalah pengaman (`<`, `<=`, `>`) yang lulus di kedua versi.

---

## Bug 10: Escape Kutip Tunggal `''` dalam String (L3)

**Ditemukan oleh:** Arif Habibi Simamora · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** Literal `'it''s'` tidak menjadi satu string bernilai `it's`; lexer berhenti di kutip penutup pertama.

**Reproduksi minimal.**

```sql
SELECT id FROM t WHERE nama = 'it''s'
```

**Akar masalah.** Lexer mengakhiri string pada kutip pertama tanpa memeriksa apakah diikuti kutip lagi. Dalam SQL, `''` di dalam string adalah escape untuk satu karakter kutip.

**Perbaikan.** `crud/lexer.py` (`104c3d3`): `''` di dalam string dibaca sebagai satu karakter kutip.

**Test regresi.** `test_l3_kutip_ganda_jadi_satu_string` (`6cf3024`): gagal di `104c3d3~1`, lulus di HEAD. `test_l3_string_biasa_tidak_berubah` adalah pengaman yang lulus di kedua versi.

---

## Bug 11: Lookup Alias Tidak dari Scope Terdalam (R1)

**Ditemukan oleh:** Arif Habibi Simamora · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** Alias yang sama (`p`) dipakai di query luar dan di subquery, lalu `p.pelanggan_id` di subquery di-resolve ke tabel yang salah.

**Reproduksi minimal.**

```sql
SELECT p.id FROM pelanggan p
WHERE p.id IN (SELECT p.pelanggan_id FROM pesanan p)
```

**Akar masalah.** Pencarian alias tidak mengikuti *lexical scoping*. Pencarian harus mulai dari scope terdalam, lalu naik ke scope induk bila tidak ketemu (Crafting Interpreters bab 11).

**Perbaikan.** `crud/resolver.py` (`bb12f84`): lookup alias dimulai dari scope terdalam.

**Test regresi.** `test_r1_alias_sama_dipakai_scope_terdalam` (`d28ada1`): gagal di `bb12f84~1` (1 failed, 1 passed), lulus di HEAD. `test_r1_alias_luar_tetap_terlihat_dari_subquery` adalah pengaman.

---

## Bug 12: Alias DELETE Bocor ke Statement Berikutnya (R2)

**Ditemukan oleh:** Arif Habibi Simamora · **Diperbaiki oleh:** Arif Habibi Simamora

**Gejala.** Setelah `DELETE FROM pelanggan ...`, statement berikutnya masih bisa me-resolve `pelanggan.nama`, padahal tabel itu tidak ada di scope-nya.

**Reproduksi minimal.**

```sql
DELETE FROM pelanggan WHERE pelanggan.id = 1;
SELECT pelanggan.nama FROM pesanan o
```

**Akar masalah.** `_delete` memanggil `_push()` tanpa `_pop()`, sehingga scope DELETE tidak pernah dilepas dan bocor ke statement berikutnya.

**Perbaikan.** `crud/resolver.py` (`b0520e6`): menambah `self._pop()` di akhir `_delete`.

**Test regresi.** `test_r2_alias_delete_tidak_bocor_ke_statement_berikutnya` (`815c066`): gagal di `b0520e6~1` (1 failed, 1 passed; hasil `[] == ['error']`), lulus di HEAD. `test_r2_delete_sendiri_tetap_teresolusi` adalah pengaman.

---

## Peran AI (Bug 6-12)

AI (Claude) dipakai untuk menyusun tes regresi Lexer dan Resolver, menyusun draf laporan ini, dan memandu pembuktian "gagal di `~1`". Bukti pertama untuk R2 dan T2 ternyata tidak valid: path hasil `git archive` salah, sehingga pytest sebenarnya jalan di HEAD (4 passed). Kami mengetahuinya dari pesan error `Copy-Item`, lalu mengulang dengan path yang benar. AI juga sempat salah menyebut sebagian entri laporan sudah ada, dan salah mengaitkan Ziddan dengan perbaikan Lexer/Resolver. Keduanya kami koreksi dengan `git log`. Verifikasi: semua klaim "gagal sebelum, lulus sesudah" berasal dari output pytest yang kami jalankan sendiri pada commit lama dan baru.