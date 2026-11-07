# Log Penggunaan AI

Catat setiap penggunaan AI atau coding agent yang memengaruhi kode atau laporan.

| No | Siapa | Prompt / tugas (ringkas) | Hasil: diterima, diubah, atau ditolak | Alasan | Cara verifikasi |
| --- | --- | --- | --- | --- | --- |
| 1 | Arif Habibi Simamora | Menyusun ground truth `audit.sql` (10 triple) dari SPESIFIKASI.md | Diterima setelah dicek | Disusun dari spesifikasi, bukan dari keluaran program, supaya evaluasi tidak melingkar | Dicocokkan ke SPESIFIKASI.md; `python evaluate.py` (parser P/R/F1 = 1.00) |
| 2 | Arif Habibi Simamora | Mengecek tes regresi P1, P2, P3, T1, A1 gagal di kode lama | Diterima | Tes regresi hanya bermakna jika gagal sebelum perbaikan | Kode lama diekstrak dengan `git archive` ke folder terpisah, pytest dijalankan sendiri |
| 3 | Arif Habibi Simamora | Hasil pengecekan: tes `NOT` (P1) ternyata lolos di kode lama | Diubah: komentar tes dikoreksi (commit `cb2347e`) | Tes itu pengaman, bukan bukti bug; komentar lama salah | Pytest di kode lama; `_not()` sudah benar sejak awal |
| 4 | Arif Habibi Simamora | Patch T1 (`INSERT ... SELECT`) | Ditolak lalu diperbaiki | Patch pertama salah dan membuat 20 tes gagal dan diperbaiki oleh Arif setelah pytest penuh dijalankan | Seluruh pytest dijalankan; patch yang berlaku lulus semua tes |
| 5 | Arif Habibi Simamora | Draf `LAPORAN_BUG.md` untuk 5 bug dari diff commit dan output pytest | Diubah | Bagian "Akar masalah" harus kata sendiri dan diuji lisan | Hash commit, nama fungsi, dan kode lama dicek dengan `git show` dan `git diff` (P1 di `bb12f84`, P2 di `84da599`, A1 di `b138b7c`) |
| 6 | Arif Habibi Simamora | Penjelasan lisan "Akar masalah" kelima bug | Diubah | Dibaca, dipahami, lalu disusun ulang dengan kalimat sendiri | Dicocokkan ke kode dan buku *Crafting Interpreters* bab 5,6 dan 11 |
| 7 | Arif Habibi Simamora | Saran alternatif perbaikan di "Perbaikan" tiap bug  | Diterima | Alasan teknisnya sesuai arsitektur di SPESIFIKASI.md | Didiskusikan dengan Ziddan dan dicocokkan dengan SPESIFIKASI.md |
| 8 | Muhammad Ziddan | Menyusun ground truth `pemeliharaan.sql` (7 triple) berdasarkan SPESIFIKASI.md | Diterima setelah dicek | Memastikan nama tabel menyertakan prefix skema `crm.` sesuai SPESIFIKASI.md bagian 5 | Jalankan `python evaluate.py` hingga parser mencapai P/R/F1 = 1.00 |
| 9 | Muhammad Ziddan | Penjelasan konsep "Akar Masalah" bug Lexer (L1, L2) dan Resolver (R1) | Diubah | Menyusun penjelasan akar masalah menggunakan istilah formal Bab 4 & 11 buku *Crafting Interpreters* | Dicocokkan dengan implementasi di `crud/lexer.py` dan `crud/resolver.py` serta pengujian pytest |
| 10 | Muhammad Ziddan | Draf Kartu Desain 4 & 5 (Hierarki Scope dan Unqualified Columns) | Diterima | Menjelaskan pilihan arsitektur beserta alternatif yang ditolak sesuai aturan scope di SPESIFIKASI.md | Memeriksa kesesuaian batasan arsitektur pada SPESIFIKASI.md Bagian 4 & 7 |
| 11 | Arif Habibi Simamora | Menyusun tes regresi Lexer dan Resolver (L1, L2, L3, T3, R1, R2, T2) dan draf laporan Bug 6-12 | Diubah | Tes dan draf disesuaikan dengan kode dan riwayat commit; klaim AI yang tidak cocok dikoreksi | Setiap tes dibuktikan gagal di commit perbaikan~1 (L1: 9b54346~1, L2: 3a5b329~1, L3: 104c3d3~1, T3: 4f5ea3c~1, R1: bb12f84~1, R2: b0520e6~1, T2: 4d9aac9~1) dengan `git archive` + pytest; nama tes dan hash dicek ke `git log` |
| 12 | Arif Habibi Simamora | Perintah AI untuk membuktikan "gagal di `~1`" untuk R2 dan T2 | Ditolak lalu diulang | Percobaan pertama tidak valid: path hasil `git archive` salah, jadi pytest berjalan di HEAD (4 passed) | Pesan error `Copy-Item` dibaca; diulang dengan path yang benar (R2: 1 failed, 1 passed; T2: 2 failed) |

**Refleksi (3-5 kalimat).** Di bagian mana AI paling membantu? Di mana AI keliru atau
menyesatkan, dan bagaimana kalian mengetahuinya?
 **Arif Habibi Simamora**: AI paling membantu untuk menyusun ground truth dari spesifikasi dan memeriksa
bahwa tes regresi benar-benar gagal di kode lama, sehingga ketahuan bahwa tes `NOT` untuk P1
hanyalah pengaman, bukan bukti bug. AI juga keliru satu perintah `git diff` yang diberikan
memakai path yang salah sehingga keluarannya kosong, dan sempat terlihat seolah perbaikan P2
tidak ada di commitnya. Kami mengetahuinya karena memeriksa langsung dengan `git show --stat`
dan `git log`. Kesalahan kami sendiri, yaitu patch pertama T1 yang membuat 20 tes gagal, juga
ketahuan dari pytest penuh. Pada tahap Lexer dan Resolver, AI sempat salah menyebut Ziddan mengerjakan
Lexer/Resolver dan salah menganggap sebagian entri laporan sudah ada. Keduanya kami ketahui dari `git log` 
dan `git show`, bukan dari klaim AI. Pelajarannya: klaim AI tentang kode dan commit harus dicek ke repo.

**Muhammad Ziddan**: AI paling membantu untuk menyusun ground truth dari spesifikasi, mengidentifikasi keharusan penulisan nama skema lengkap (`crm.pelanggan`), dan memberikan referensi konsep formal dari buku *Crafting Interpreters* (Bab 4, 6, dan 11) untuk penjelasan akar masalah. AI sempat keliru saat memberikan format ground truth awal tanpa prefix skema `crm.`, yang menyebabkan nilai evaluasi parser sempat turun menjadi 0.74. Kami mengetahuinya dengan melakukan cross-check langsung ke SPESIFIKASI.md bagian 5 dan memeriksa keluaran `python evaluate.py`. Pelajarannya: setiap saran dan draf keluaran dari AI wajib diverifikasi ulang terhadap dokumen acuan kebenaran dan pengujian lokal.

