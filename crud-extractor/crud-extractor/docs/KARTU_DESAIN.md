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
| 4 | (Ziddan) urutan pencarian scope dan akibatnya pada shadowing / correlated subquery | (isi Ziddan) | (isi Ziddan) |
| 5 | (Ziddan) kolom tanpa qualifier hanya di-resolve ke scope terdalam (T2), dan kelemahannya | (isi Ziddan) | (isi Ziddan) |
