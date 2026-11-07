# Kartu Desain

Tuliskan lima keputusan desain penting dalam pekerjaan kalian. Untuk tiap keputusan, sebutkan
alternatif yang ditolak dan alasannya. Contoh topik (boleh memilih yang lain):

- bagaimana parser membedakan `*` sebagai "semua kolom" dan sebagai perkalian;
- di mana dan bagaimana presedensi `AND`/`OR` dinyatakan;
- mengapa error recovery berhenti di `;`, bukan di keyword `SELECT` berikutnya;
- urutan pencarian scope dan akibatnya pada shadowing serta correlated subquery;
- mengapa kolom tanpa qualifier hanya dilihat di scope terdalam, dan apa kelemahannya;
- bagaimana implementasi `INSERT ... SELECT` atau komentar blok kalian.

| No | Keputusan | Alternatif yang ditolak | Alasan |
| --- | --- | --- | --- |
| 1 | `*` dibedakan lewat posisi dalam grammar, bukan lewat token: `_select_list` memeriksa `*` di awal daftar kolom (jadi `Star`), `_function_call` menangani `COUNT(*)`, dan `_multiplicative` membaca `*` sebagai perkalian | Membuat lexer menghasilkan dua jenis token berbeda untuk `*` | Lexer tidak tahu konteks; hanya parser yang tahu `*` berada di posisi daftar kolom atau di tengah ekspresi |
| 2 | Presedensi `AND`/`OR` dinyatakan lewat rantai fungsi `_or()` → `_and()` → `_not()` | Tabel presedensi dengan precedence climbing (Pratt parser) | Seluruh parser sudah memakai gaya satu-fungsi-per-tingkat; mengganti satu bagian membuat kode tidak seragam |
| 3 | Error recovery berhenti **setelah** `;` (`_synchronize` return setelah mengonsumsi `SEMICOLON`) | Berhenti di keyword awal statement (`SELECT`, `INSERT`, dst.) | Keyword itu bisa muncul di dalam subquery; spesifikasi bagian 6 menyebut `;` secara eksplisit; `;` milik statement yang rusak, jadi ikut dibuang |
| 4 | Lookup alias/tabel dicari mulai dari scope terdalam ke scope luar (*lexical scoping* dengan *stack of environments*) | Symbol table flat / dict global tunggal | Dict global akan menyebabkan *shadowing bug* (alias subquery menimpa alias query luar secara permanen) dan tidak bisa mendukung resolusi *correlated subquery* (SPESIFIKASI 4.1–4.3) |
| 5 | Kolom tanpa kualifikasi (*unqualified column*) hanya di-resolve di scope terdalam: jika tepat ada 1 tabel otomatis terikat, jika >1 tabel ditandai ambigu (`resolved = None`) | 1. Mencari hingga scope luar. 2. Selalu menyetel `resolved = None` | 1. Melanggar SPESIFIKASI 4.3 yang melarang pencarian ke scope luar. Kelemahannya: gagal me-resolve kolom pada query multi-tabel tanpa prefix (butuh skema DB formal). 2. Merusak analisis penggunaan kolom pada query 1 tabel. |